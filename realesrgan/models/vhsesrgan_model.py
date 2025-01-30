import numpy as np
import random
import torch
from basicsr.data.degradations import random_add_gaussian_noise_pt, random_add_poisson_noise_pt
from basicsr.data.transforms import paired_random_crop
from basicsr.models.srgan_model import SRGANModel
from basicsr.utils.img_process_util import filter2D
from basicsr.utils.registry import MODEL_REGISTRY
from collections import OrderedDict
from realesrgan.archs.srvgg_arch import SRVGGNetCompact
from torch.nn import functional as F
from torchvision.transforms import v2

@MODEL_REGISTRY.register()
class VHSESRGANModel(SRGANModel):
    """VHSESRGAN Model for VHS ESRGAN: Training Super-Resolution for VHS tapes.

    It mainly performs:
    1. randomly synthesize LQ images using a pretrained HQ->LQ network.
    2. optimize the networks with GAN training.
    """

    def __init__(self, opt):
        super(VHSESRGANModel, self).__init__(opt)
        self.queue_size = opt.get('queue_size', 180)
        
        degradation_model_path = opt.get('degradation_model_g', None)
        if degradation_model_path:
            # Initialize our degradation model, which we're going to use instead of the various
            # blur and noise functions employed by RealESRGAN.
            print('Loading model ', degradation_model_path)
            # TODO: Fixed parameter set. Could read this from a config or autodetect.
            self.deg_model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64,
                                             num_conv=16, upscale=1, act_type='prelu')
            loadnet = torch.load(degradation_model_path, map_location=torch.device('cpu'))
            # prefer to use params_ema (because everybody else does ^^)
            if 'params_ema' in loadnet:
                keyname = 'params_ema'
            else:
                keyname = 'params'
            self.deg_model.load_state_dict(loadnet[keyname], strict=True)
            self.deg_model.eval()
            self.deg_model = self.deg_model.to(self.device)

            # TODO: Make this configurable.
            self.color_jitter = v2.ColorJitter(brightness=.5, contrast=.5, saturation=.5, hue=.5)
            self.random_rotation = v2.RandomRotation(degrees=(0,180))
            self.random_transforms = v2.Compose([
                v2.RandomHorizontalFlip(p=self.opt['horiz_flip_prob']),
                v2.RandomPerspective(distortion_scale=0.6, p=self.opt['perspective_prob'])
            ])

    @torch.no_grad()
    def _dequeue_and_enqueue(self):
        """It is the training pair pool for increasing the diversity in a batch.

        Batch processing limits the diversity of synthetic degradations in a batch. For example, samples in a
        batch could not have different resize scaling factors. Therefore, we employ this training pair pool
        to increase the degradation diversity in a batch.
        """
        # initialize
        b, c, h, w = self.lq.size()
        if not hasattr(self, 'queue_lr'):
            assert self.queue_size % b == 0, f'queue size {self.queue_size} should be divisible by batch size {b}'
            self.queue_lr = torch.zeros(self.queue_size, c, h, w).cuda()
            _, c, h, w = self.gt.size()
            self.queue_gt = torch.zeros(self.queue_size, c, h, w).cuda()
            self.queue_ptr = 0
        if self.queue_ptr == self.queue_size:  # the pool is full
            # do dequeue and enqueue
            # shuffle
            idx = torch.randperm(self.queue_size)
            self.queue_lr = self.queue_lr[idx]
            self.queue_gt = self.queue_gt[idx]
            # get first b samples
            lq_dequeue = self.queue_lr[0:b, :, :, :].clone()
            gt_dequeue = self.queue_gt[0:b, :, :, :].clone()
            # update the queue
            self.queue_lr[0:b, :, :, :] = self.lq.clone()
            self.queue_gt[0:b, :, :, :] = self.gt.clone()

            self.lq = lq_dequeue
            self.gt = gt_dequeue
        else:
            # only do enqueue
            self.queue_lr[self.queue_ptr:self.queue_ptr + b, :, :, :] = self.lq.clone()
            self.queue_gt[self.queue_ptr:self.queue_ptr + b, :, :, :] = self.gt.clone()
            self.queue_ptr = self.queue_ptr + b

    @torch.no_grad()
    def feed_data(self, data):
        """Accept data from dataloader, and then add two-order degradations to obtain LQ images.
        """
        if self.is_train and self.opt.get('high_order_degradation', True):
            # training data synthesis
            self.gt = data['gt'].to(self.device)

            ori_h, ori_w = self.gt.size()[2:4]

            # Before we even generate the downscaled image, let's do some nasty things to the original
            # to diversify the dataset.
            color_jitter_prob = self.opt['color_jitter_prob']
            if np.random.uniform() < color_jitter_prob:
                self.gt=self.color_jitter(self.gt)
            rotation_prob = self.opt['rotation_prob']
            if np.random.uniform() < rotation_prob:
                self.gt=self.random_rotation(self.gt)

            # Apply the rest of the preconfigured transforms (their probability is preconfigured
            # through the configuration).
            self.gt=self.random_transforms(self.gt)                

            # With VHS degradation, we always want the degradation to be applied to the final size LQ
            # image (downscaled to opt['scale']), so this is what we'll do first.
            
            # resize back + the final sinc filter
            mode = random.choice(['area', 'bilinear', 'bicubic'])
            self.lq = F.interpolate(self.gt, size=(ori_h // self.opt['scale'], ori_w // self.opt['scale']), mode=mode)

            # random crop
            gt_size = self.opt['gt_size']
            self.gt, self.lq = paired_random_crop(self.gt, self.lq, gt_size, self.opt['scale'])
            
            # Run the VHS degradation network once, twice or three times.
            if self.deg_model:
                num_deg = random.choice([1,2,3])
                for _ in range(0,num_deg):
                    self.lq = self.deg_model(self.lq)

            # Add some additional noise so irrelevant invariants learned by the degradation model don't
            # transfer to the upscaling model.
            gray_noise_prob = self.opt['gray_noise_prob']
            if np.random.uniform() < self.opt['gaussian_noise_prob']:
                self.lq = random_add_gaussian_noise_pt(
                    self.lq, sigma_range=self.opt['noise_range'], clip=True,
                    rounds=False, gray_prob=gray_noise_prob)
            else:
                self.lq = random_add_poisson_noise_pt(
                    self.lq,
                    scale_range=self.opt['poisson_scale_range'],
                    gray_prob=gray_noise_prob,
                    clip=True,
                    rounds=False)

            # clamp and round
            self.lq = torch.clamp((self.lq * 255.0).round(), 0, 255) / 255.

            # training pair pool
            self._dequeue_and_enqueue()
            self.lq = self.lq.contiguous()  # for the warning: grad and param do not obey the gradient layout contract
        else:
            # for paired training or validation
            self.lq = data['lq'].to(self.device)
            if 'gt' in data:
                self.gt = data['gt'].to(self.device)

    def nondist_validation(self, dataloader, current_iter, tb_logger, save_img):
        # do not use the synthetic process during validation
        self.is_train = False
        super(VHSESRGANModel, self).nondist_validation(dataloader, current_iter, tb_logger, save_img)
        self.is_train = True

    def optimize_parameters(self, current_iter):
        l1_gt = self.gt
        percep_gt = self.gt
        gan_gt = self.gt

        # optimize net_g
        for p in self.net_d.parameters():
            p.requires_grad = False

        self.optimizer_g.zero_grad()
        self.output = self.net_g(self.lq)

        l_g_total = 0
        loss_dict = OrderedDict()
        if (current_iter % self.net_d_iters == 0 and current_iter > self.net_d_init_iters):
            # pixel loss
            if self.cri_pix:
                l_g_pix = self.cri_pix(self.output, l1_gt)
                l_g_total += l_g_pix
                loss_dict['l_g_pix'] = l_g_pix
            # perceptual loss
            if self.cri_perceptual:
                l_g_percep, l_g_style = self.cri_perceptual(self.output, percep_gt)
                if l_g_percep is not None:
                    l_g_total += l_g_percep
                    loss_dict['l_g_percep'] = l_g_percep
                if l_g_style is not None:
                    l_g_total += l_g_style
                    loss_dict['l_g_style'] = l_g_style
            # gan loss
            fake_g_pred = self.net_d(self.output)
            l_g_gan = self.cri_gan(fake_g_pred, True, is_disc=False)
            l_g_total += l_g_gan
            loss_dict['l_g_gan'] = l_g_gan

            l_g_total.backward()
            self.optimizer_g.step()

        # optimize net_d
        for p in self.net_d.parameters():
            p.requires_grad = True

        self.optimizer_d.zero_grad()
        # real
        real_d_pred = self.net_d(gan_gt)
        l_d_real = self.cri_gan(real_d_pred, True, is_disc=True)
        loss_dict['l_d_real'] = l_d_real
        loss_dict['out_d_real'] = torch.mean(real_d_pred.detach())
        l_d_real.backward()
        # fake
        fake_d_pred = self.net_d(self.output.detach().clone())  # clone for pt1.9
        l_d_fake = self.cri_gan(fake_d_pred, False, is_disc=True)
        loss_dict['l_d_fake'] = l_d_fake
        loss_dict['out_d_fake'] = torch.mean(fake_d_pred.detach())
        l_d_fake.backward()
        self.optimizer_d.step()

        if self.ema_decay > 0:
            self.model_ema(decay=self.ema_decay)

        self.log_dict = self.reduce_loss_dict(loss_dict)
