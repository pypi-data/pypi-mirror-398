import pyro
import pyro.distributions as dist
from pyro.optim import ExponentialLR
from pyro.infer import SVI, JitTraceEnum_ELBO, TraceEnum_ELBO, config_enumerate

import scvi.distributions as scvi_dist 

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.distributions.utils import logits_to_probs, probs_to_logits, clamp_probs
from torch.distributions import constraints
from torch.distributions.transforms import SoftmaxTransform

from .utils.custom_mlp import MLP, Exp, ZeroBiasMLP, ZeroBiasMLP2, ZeroBiasMLP3
from .utils.utils import CustomDataset, CustomDataset2, CustomDataset3, tensor_to_numpy, convert_to_tensor

from .dist.negbinomial import NegativeBinomial as MyNB
from .dist.negbinomial import ZeroInflatedNegativeBinomial as MyZINB

import zuko 
from pyro.contrib.zuko import ZukoToPyro

import os
import argparse
import random
import numpy as np
import datatable as dt
from tqdm import tqdm
from scipy import sparse

import scanpy as sc
from .atac import binarize

from typing import Literal

import warnings
warnings.filterwarnings("ignore")

import dill as pickle
import gzip
from packaging.version import Version
torch_version = torch.__version__


def set_random_seed(seed):
    # Set seed for PyTorch
    torch.manual_seed(seed)
    
    # If using CUDA, set the seed for CUDA
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # For multi-GPU setups.
    
    # Set seed for NumPy
    np.random.seed(seed)
    
    # Set seed for Python's random module
    random.seed(seed)

    # Set seed for Pyro
    pyro.set_rng_seed(seed)

class DensityFlowNSF(nn.Module):
    """DensityFlowNSF model

    Parameters
    ----------
    input_dim : int
        Number of features like genes or peaks

    codebook_size: int
        Number of codebook items

    perturb_size: int
        Number of perturbations
    
    cov_size: int
        Number of covariates

    specific_mode: str
        Type of specificity mode. Either 'none', 'codebook', or 'cell'. 'none' will
        use uniform perturbation effects. 'codebook' will learn cell-state-specific
        perturbation effects. 'cell' will learn cell-specific perturbation effects. 

    z_dim : int
        Dimensionality of latent space.

    z_dist: str
        Distribution model of latent variable. One of 'normal', 'studentt', 'laplacian',
        'cauchy', and 'gumbel'. Default is 'studentt'.
        
    loss_func: str
        Distribution model for observed profiles. One of 'negbinomial', 'poisson', 'multinomial',
        'bernoulli'. Default is 'poisson'


    Examples
    --------
    >>> from DensityFlowNSF import DensityFlowNSF
    >>> from DensityFlowNSF.perturb import LabelMatrix
    >>> import scanpy as sc
    >>> adata = sc.read('dataset.h5ad')
    >>> adata.X = adata.layers['counts].copy()
    >>> sc.pp.normalize_total(adata)
    >>> sc.pp.log1p(adata)
    >>> xs = adata.X 
    >>> lb = LabelMatrix()
    >>> us = lb.fit_transform(adata_train.obs[pert_col], control_label=control_label)
    >>> ln = lb.labels_
    >>> model = DensityFlowNSF(input_dim = xs.shape[1],
                            perturb_size=us.shape[1],
                            use_cuda=True)
    >>> model.fit(xs, us=us, use_jax=True)
    >>> zs_basal = model.get_basal_embedding(xs)
    >>> zs_complete = model.get_complete_embedding(xs, us)
    """
    def __init__(self,
                 input_dim: int,
                 codebook_size: int = 15,
                 perturb_size: int = 0,
                 perturb_classes: int = 0,
                 cov_size: int = 0,
                 specific_mode: Literal['none','codebook','cell'] = 'codebook',
                 transforms: int = 1,
                 z_dim: int = 50,
                 z_dist: Literal['normal','studentt','laplacian','cauchy','gumbel'] = 'studentt',
                 loss_func: Literal['negbinomial','poisson','multinomial','bernoulli'] = 'poisson',
                 dispersion: float = 10.0,
                 use_zeroinflate: bool = False,
                 hidden_layers: list = [512],
                 hidden_layer_activation: Literal['relu','softplus','leakyrelu','linear'] = 'relu',
                 flow_hidden_layers: list = [128,128,128],
                 nn_dropout: float = 0.1,
                 post_layer_fct: list = ['layernorm'],
                 post_act_fct: list = None,
                 config_enum: str = 'parallel',
                 use_cuda: bool = True,
                 seed: int = 42,
                 dtype = torch.float32, # type: ignore
                 ):
        super().__init__()

        self.input_dim = input_dim
        self.perturb_size = perturb_size
        self.perturb_classes = perturb_classes
        self.cov_size = cov_size
        self.dispersion = dispersion
        self.latent_dim = z_dim
        self.hidden_layers = hidden_layers
        self.decoder_hidden_layers = hidden_layers[::-1]
        self.config_enum = config_enum
        self.allow_broadcast = config_enum == 'parallel'
        self.use_cuda = use_cuda
        self.loss_func = loss_func
        self.options = None
        self.code_dim=codebook_size
        self.latent_dist = z_dist
        self.dtype = dtype
        self.use_zeroinflate=use_zeroinflate
        self.nn_dropout = nn_dropout
        self.post_layer_fct = post_layer_fct
        self.post_act_fct = post_act_fct
        self.hidden_layer_activation = hidden_layer_activation
        self.specific_mode = specific_mode
        self.transforms = transforms
        self.flow_hidden_layers = flow_hidden_layers
        
        self.codebook_weights = None

        self.seed = seed
        set_random_seed(seed)
        self.setup_networks()
        
        print(f"🧬 DensityFlowNSF Initialized:")
        print(f"   - Codebook size: {self.code_dim}")
        print(f"   - Latent Dimension: {self.latent_dim}")
        print(f"   - Gene Dimension: {self.input_dim}")
        print(f"   - Hidden Dimensions: {self.hidden_layers}")
        print(f"   - Device: {self.get_device()}")
        print(f"   - Parameters: {sum(p.numel() for p in self.parameters()):,}")

    def setup_networks(self):
        latent_dim = self.latent_dim
        hidden_sizes = self.hidden_layers

        nn_layer_norm, nn_batch_norm, nn_layer_dropout = False, False, False
        na_layer_norm, na_batch_norm, na_layer_dropout = False, False, False

        if self.post_layer_fct is not None:
            nn_layer_norm=True if ('layernorm' in self.post_layer_fct) or ('layer_norm' in self.post_layer_fct) else False
            nn_batch_norm=True if ('batchnorm' in self.post_layer_fct) or ('batch_norm' in self.post_layer_fct) else False
            nn_layer_dropout=True if 'dropout' in self.post_layer_fct else False

        if self.post_act_fct is not None:
            na_layer_norm=True if ('layernorm' in self.post_act_fct) or ('layer_norm' in self.post_act_fct) else False
            na_batch_norm=True if ('batchnorm' in self.post_act_fct) or ('batch_norm' in self.post_act_fct) else False
            na_layer_dropout=True if 'dropout' in self.post_act_fct else False

        if nn_layer_norm and nn_batch_norm and nn_layer_dropout:
            post_layer_fct = lambda layer_ix, total_layers, layer: nn.Sequential(nn.Dropout(self.nn_dropout),nn.BatchNorm1d(layer.module.out_features), nn.LayerNorm(layer.module.out_features))
        elif nn_layer_norm and nn_layer_dropout:
            post_layer_fct = lambda layer_ix, total_layers, layer: nn.Sequential(nn.Dropout(self.nn_dropout), nn.LayerNorm(layer.module.out_features))
        elif nn_batch_norm and nn_layer_dropout:
            post_layer_fct = lambda layer_ix, total_layers, layer: nn.Sequential(nn.Dropout(self.nn_dropout), nn.BatchNorm1d(layer.module.out_features))
        elif nn_layer_norm and nn_batch_norm:
            post_layer_fct = lambda layer_ix, total_layers, layer: nn.Sequential(nn.BatchNorm1d(layer.module.out_features), nn.LayerNorm(layer.module.out_features))
        elif nn_layer_norm:
            post_layer_fct = lambda layer_ix, total_layers, layer: nn.LayerNorm(layer.module.out_features)
        elif nn_batch_norm:
            post_layer_fct = lambda layer_ix, total_layers, layer:nn.BatchNorm1d(layer.module.out_features)
        elif nn_layer_dropout:
            post_layer_fct = lambda layer_ix, total_layers, layer: nn.Dropout(self.nn_dropout)
        else:
            post_layer_fct = lambda layer_ix, total_layers, layer: None

        if na_layer_norm and na_batch_norm and na_layer_dropout:
            post_act_fct = lambda layer_ix, total_layers, layer: nn.Sequential(nn.Dropout(self.nn_dropout),nn.BatchNorm1d(layer.module.out_features), nn.LayerNorm(layer.module.out_features))
        elif na_layer_norm and na_layer_dropout:
            post_act_fct = lambda layer_ix, total_layers, layer: nn.Sequential(nn.Dropout(self.nn_dropout), nn.LayerNorm(layer.module.out_features))
        elif na_batch_norm and na_layer_dropout:
            post_act_fct = lambda layer_ix, total_layers, layer: nn.Sequential(nn.Dropout(self.nn_dropout), nn.BatchNorm1d(layer.module.out_features))
        elif na_layer_norm and na_batch_norm:
            post_act_fct = lambda layer_ix, total_layers, layer: nn.Sequential(nn.BatchNorm1d(layer.module.out_features), nn.LayerNorm(layer.module.out_features))
        elif na_layer_norm:
            post_act_fct = lambda layer_ix, total_layers, layer: nn.LayerNorm(layer.module.out_features)
        elif na_batch_norm:
            post_act_fct = lambda layer_ix, total_layers, layer:nn.BatchNorm1d(layer.module.out_features)
        elif na_layer_dropout:
            post_act_fct = lambda layer_ix, total_layers, layer: nn.Dropout(self.nn_dropout)
        else:
            post_act_fct = lambda layer_ix, total_layers, layer: None

        if self.hidden_layer_activation == 'relu':
            activate_fct = nn.ReLU
        elif self.hidden_layer_activation == 'softplus':
            activate_fct = nn.Softplus
        elif self.hidden_layer_activation == 'leakyrelu':
            activate_fct = nn.LeakyReLU
        elif self.hidden_layer_activation == 'linear':
            activate_fct = nn.Identity

        self.encoder_n = MLP(
                [self.latent_dim] + hidden_sizes + [self.code_dim],
                activation=activate_fct,
                output_activation=None,
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )

        '''self.encoder_zn = MLP(
            [self.input_dim] + hidden_sizes + [[latent_dim, latent_dim]],
            activation=activate_fct,
            output_activation=[None, Exp],
            post_layer_fct=post_layer_fct,
            post_act_fct=post_act_fct,
            allow_broadcast=self.allow_broadcast,
            use_cuda=self.use_cuda,
        )'''

        if self.cov_size>0:
            self.covariate_effect = ZeroBiasMLP2(
                [self.cov_size] + self.decoder_hidden_layers + [self.latent_dim],
                activation=activate_fct,
                output_activation=None,
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )
            
        if self.perturb_size>0:
            if self.specific_mode=='none':
                self.perturb_effect = ZeroBiasMLP3(
                    [self.perturb_size+self.perturb_classes] + self.decoder_hidden_layers + [self.latent_dim],
                    activation=activate_fct,
                    output_activation=None,
                    post_layer_fct=post_layer_fct,
                    post_act_fct=post_act_fct,
                    allow_broadcast=self.allow_broadcast,
                    use_cuda=self.use_cuda,
                )
            else:
                self.perturb_effect = ZeroBiasMLP3(
                    [self.perturb_size+self.perturb_classes+self.latent_dim] + self.decoder_hidden_layers + [self.latent_dim],
                    activation=activate_fct,
                    output_activation=None,
                    post_layer_fct=post_layer_fct,
                    post_act_fct=post_act_fct,
                    allow_broadcast=self.allow_broadcast,
                    use_cuda=self.use_cuda,
                )
            
        self.decoder_log_mu = MLP(
                    [self.latent_dim] + self.decoder_hidden_layers + [self.input_dim],
                    activation=activate_fct,
                    output_activation=None,
                    post_layer_fct=post_layer_fct,
                    post_act_fct=post_act_fct,
                    allow_broadcast=self.allow_broadcast,
                    use_cuda=self.use_cuda,
                )

        if self.latent_dist == 'studentt':
            self.codebook = MLP(
                [self.code_dim] + hidden_sizes + [[latent_dim,latent_dim]],
                activation=activate_fct,
                output_activation=[Exp,None],
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )
        else:
            self.codebook = MLP(
                [self.code_dim] + hidden_sizes + [latent_dim],
                activation=activate_fct,
                output_activation=None,
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )
        
        self.encoder_zn = zuko.flows.NSF(features=self.latent_dim, context=self.input_dim, 
                                         transforms=self.transforms, hidden_features=self.flow_hidden_layers)
        
        if self.use_cuda:
            self.cuda()

    def get_device(self):
        return next(self.parameters()).device

    def cutoff(self, xs, thresh=None):
        eps = torch.finfo(xs.dtype).eps
        
        if not thresh is None:
            if eps < thresh:
                eps = thresh

        xs = xs.clamp(min=eps)

        if torch.any(torch.isnan(xs)):
            xs[torch.isnan(xs)] = eps

        return xs

    def softmax(self, xs):
        #xs = SoftmaxTransform()(xs)
        xs = dist.Multinomial(total_count=1, logits=xs).mean
        return xs
    
    def sigmoid(self, xs):
        #sigm_enc = nn.Sigmoid()
        #xs = sigm_enc(xs)
        #xs = clamp_probs(xs)
        xs = dist.Bernoulli(logits=xs).mean
        return xs

    def softmax_logit(self, xs):
        eps = torch.finfo(xs.dtype).eps
        xs = self.softmax(xs)
        xs = torch.logit(xs, eps=eps)
        return xs

    def logit(self, xs):
        eps = torch.finfo(xs.dtype).eps
        xs = torch.logit(xs, eps=eps)
        return xs

    def dirimulti_param(self, xs):
        xs = self.dirimulti_mass * self.sigmoid(xs)
        return xs

    def multi_param(self, xs):
        xs = self.softmax(xs)
        return xs

    def model(self, xs, us=None, ts=None, cs=None):
        pyro.module('DensityFlowNSF', self)

        eps = torch.finfo(xs.dtype).eps
        batch_size = xs.size(0)
        self.options = dict(dtype=xs.dtype, device=xs.device)
        
        if self.loss_func=='negbinomial':
            dispersion = pyro.param("dispersion", self.dispersion *
                                            xs.new_ones(self.input_dim), constraint=constraints.positive)
            
        if self.use_zeroinflate:
            gate_logits = pyro.param("dropout_rate", xs.new_zeros(self.input_dim))
            
        acs_scale = pyro.param("codebook_scale", xs.new_ones(self.latent_dim), constraint=constraints.positive)

        I = torch.eye(self.code_dim)
        if self.latent_dist=='studentt':
            acs_dof,acs_loc = self.codebook(I)
        else:
            acs_loc = self.codebook(I)
            
        with pyro.plate('data'):
            prior = torch.zeros(batch_size, self.code_dim, **self.options)
            ns = pyro.sample('n', dist.OneHotCategorical(logits=prior))

            zn_loc = torch.matmul(ns,acs_loc)
            #zn_scale = torch.matmul(ns,acs_scale)
            zn_scale = acs_scale

            if self.latent_dist == 'studentt':
                prior_dof = torch.matmul(ns,acs_dof)
                zns = pyro.sample('zn', dist.StudentT(df=prior_dof, loc=zn_loc, scale=zn_scale).to_event(1))
            elif self.latent_dist == 'laplacian':
                zns = pyro.sample('zn', dist.Laplace(zn_loc, zn_scale).to_event(1))
            elif self.latent_dist == 'cauchy':
                zns = pyro.sample('zn', dist.Cauchy(zn_loc, zn_scale).to_event(1))
            elif self.latent_dist == 'normal':
                zns = pyro.sample('zn', dist.Normal(zn_loc, zn_scale).to_event(1))
            elif self.latent_dist == 'gumbel':
                zns = pyro.sample('zn', dist.Gumbel(zn_loc, zn_scale).to_event(1))

            zs = zns
            if self.perturb_size>0:
                if self.specific_mode=='codebook':
                    zus = self._total_effects(zn_loc, us, ts)
                else:
                    zus = self._total_effects(zns, us, ts)
                zs = zs+zus
                
            if self.cov_size>0:
                zcs = self.covariate_effect(cs)
                zs = zs + zcs

            log_mu = self.decoder_log_mu(zs)
            if self.loss_func in ['bernoulli']:
                log_theta = log_mu
            elif self.loss_func == 'negbinomial':
                mu = log_mu.exp()
                
                #dispersion = self.decoder_dispersion(zs)
                #dispersion = dispersion.exp()
            else:
                rate = log_mu.exp()
                theta = dist.DirichletMultinomial(total_count=1, concentration=rate).mean
                if self.loss_func == 'poisson':
                    rate = theta * torch.sum(xs, dim=1, keepdim=True)

            if self.loss_func == 'negbinomial':
                if self.specific_mode=='codebook':
                    logits = (mu.log()-dispersion.log()).clamp(min=-15, max=15)
                    if self.use_zeroinflate:
                        pyro.sample('x', 
                                    dist.ZeroInflatedDistribution(dist.NegativeBinomial(total_count=dispersion, logits=logits),
                                                                  gate_logits=gate_logits).to_event(1), 
                                    obs=xs)
                    else:
                        pyro.sample('x', dist.NegativeBinomial(total_count=dispersion, logits=logits).to_event(1), obs=xs)
                else:
                    if self.use_zeroinflate:
                        pyro.sample("x", MyZINB(mu=mu, theta=dispersion, zi_logits=gate_logits).to_event(1), obs=xs)
                    else:
                        pyro.sample("x", MyNB(mu=mu, theta=dispersion).to_event(1), obs=xs)
            elif self.loss_func == 'poisson':
                if self.use_zeroinflate:
                    pyro.sample('x', dist.ZeroInflatedDistribution(dist.Poisson(rate=rate),gate_logits=gate_logits).to_event(1), obs=xs.round())
                else:
                    pyro.sample('x', dist.Poisson(rate=rate).to_event(1), obs=xs.round())
            elif self.loss_func == 'multinomial':
                pyro.sample('x', dist.Multinomial(total_count=int(1e8), probs=theta), obs=xs)
            elif self.loss_func == 'bernoulli':
                if self.use_zeroinflate:
                    pyro.sample('x', dist.ZeroInflatedDistribution(dist.Bernoulli(logits=log_theta),gate_logits=gate_logits).to_event(1), obs=xs)
                else:
                    pyro.sample('x', dist.Bernoulli(logits=log_theta).to_event(1), obs=xs)

    def guide(self, xs, us=None, ts=None, cs=None):
        with pyro.plate('data'):
            #zn_loc, zn_scale = self.encoder_zn(xs)
            #zn_loc, zn_scale = self._get_basal_embedding(xs)
            #zns = pyro.sample('zn', dist.Normal(zn_loc, zn_scale).to_event(1))
            zns = pyro.sample('zn', ZukoToPyro(self.encoder_zn(xs)))

            alpha = self.encoder_n(zns)
            ns = pyro.sample('n', dist.OneHotCategorical(logits=alpha))

    def _total_effects(self, zs, us, ts):
        zus = self._cell_shift(zs, us, ts)
        return zus
                        
    def _get_codebook_identity(self):
        return torch.eye(self.code_dim, **self.options)
    
    def _get_codebook(self):
        I = torch.eye(self.code_dim, **self.options)
        if self.latent_dist=='studentt':
            _,cb = self.codebook(I)
        else:
            cb = self.codebook(I)
        return cb
    
    def get_codebook(self):
        """
        Return the mean part of metacell codebook
        """
        cb = self._get_codebook()
        cb = tensor_to_numpy(cb)
        return cb

    def _codebook_map(self, xs, soft_assign):
        if soft_assign:
            ns = self._soft_assignments(xs)
        else:
            ns = self._hard_assignments(xs)
        cb = self._get_codebook()
        zs = torch.matmul(ns, cb)
        return zs
    
    def codebook_map(self, xs, soft_assign: bool=True, batch_size:int=1024, show_progress=True):
        xs = self.preprocess(xs)
        xs = convert_to_tensor(xs, device='cpu')
        dataset = CustomDataset(xs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                zns = self._codebook_map(X_batch, soft_assign)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z
    
    def _get_complete_embedding(self, xs, us, ts):
        basal = self._get_basal_embedding(xs)
        dzs = self._total_effects(basal, us, ts)
        return basal + dzs 
    
    def get_complete_embedding(self, xs, us, ts, batch_size:int=1024, show_progress=True):
        xs = self.preprocess(xs)
        xs = convert_to_tensor(xs, device='cpu')
        us = convert_to_tensor(us, device='cpu')
        ts = convert_to_tensor(ts, device='cpu')
        dataset = CustomDataset(xs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, idx in dataloader:
                X_batch = X_batch.to(self.get_device())
                U_batch = us[idx].to(self.get_device())
                T_batch = ts[idx].to(self.get_device())
                zns = self._get_complete_embedding(X_batch, U_batch, T_batch)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z

    def _get_basal_embedding(self, xs):           
        loc = self.encoder_zn(xs).sample((10,)).mean(axis=0)
        return loc
    
    def get_basal_embedding(self, 
                             xs, 
                             batch_size: int = 1024,
                             show_progress=True):
        """
        Return cells' basal latent representations

        Parameters
        ----------
        xs: numpy.array
            Single-cell expression matrix. It should be a Numpy array or a Pytorch Tensor
        batch_size: int
            Size of batch processing
        show_progress: bool
            Verbose on or off
        """
        xs = self.preprocess(xs)
        xs = convert_to_tensor(xs, device='cpu')
        dataset = CustomDataset(xs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                zns = self._get_basal_embedding(X_batch)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z
    
    def _code(self, xs):
        zns = self._get_basal_embedding(xs)
        alpha = self.encoder_n(zns)
        return alpha
    
    def code(self, xs, batch_size=1024, show_progress=True):
        xs = self.preprocess(xs)
        xs = convert_to_tensor(xs, device='cpu')
        dataset = CustomDataset(xs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        A = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                a = self._code(X_batch)
                A.append(tensor_to_numpy(a))
                pbar.update(1)

        A = np.concatenate(A)
        return A
    
    def _soft_assignments(self, xs):
        alpha = self._code(xs)
        alpha = self.softmax(alpha)
        return alpha
    
    def soft_assignments(self, xs, batch_size=1024, show_progress=True):
        """
        Map cells to metacells and return the probabilistic values of metacell assignments
        """
        xs = self.preprocess(xs)
        xs = convert_to_tensor(xs, device='cpu')
        dataset = CustomDataset(xs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        A = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                a = self._soft_assignments(X_batch)
                A.append(tensor_to_numpy(a))
                pbar.update(1)

        A = np.concatenate(A)
        return A
    
    def _hard_assignments(self, xs):
        alpha = self._code(xs)
        res, ind = torch.topk(alpha, 1)
        ns = torch.zeros_like(alpha).scatter_(1, ind, 1.0)
        return ns
    
    def hard_assignments(self, xs, batch_size=1024, show_progress=True):
        """
        Map cells to metacells and return the assigned metacell identities.
        """
        xs = self.preprocess(xs)
        xs = convert_to_tensor(xs, device='cpu')
        dataset = CustomDataset(xs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        A = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                a = self._hard_assignments(X_batch)
                A.append(tensor_to_numpy(a))
                pbar.update(1)

        A = np.concatenate(A)
        return A
    
    def predict(self, xs, perturb, perturb_type, library_sizes=None, show_progress=True):
        perturbs_reference = np.array(perturbs_reference)
        perturbs_predict = np.unique(perturbs_predict)
        
        # basal embedding
        zs = self.get_basal_embedding(xs)
        
        # shift
        dzs = self.get_cell_shift(xs, perturb_us=perturb, perturb_type=perturb_type, show_progress=show_progress)          
        
        zs = zs + dzs
        
        if library_sizes is None:
            library_sizes = np.sum(xs, axis=1, keepdims=True)
        elif type(library_sizes) == list:
            library_sizes = np.array(library_sizes)
            library_sizes = library_sizes.reshape(-1,1)
        elif len(library_sizes.shape)==1:
            library_sizes = library_sizes.reshape(-1,1)
            
        counts = self.get_counts(zs, library_sizes=library_sizes, show_progress=show_progress)
        log_mu = self.get_log_mu(zs, show_progress=show_progress)
        
        return counts, log_mu
    
    def _cell_shift(self, zs, perturb, perturb_type):
        if self.specific_mode=='none':
            ms = self.perturb_effect([perturb, perturb_type])
        else:
            ms = self.perturb_effect([perturb, perturb_type, zs])
        return ms 

    def get_cell_shift(self, 
                             xs, 
                             perturb_us,
                             perturb_type,
                             soft_assign: bool = True,
                             batch_size: int = 1024,
                             show_progress=True):
        """
        Compute displacement vector induced by a perturbation.
        
        Parameters
        ----------
        xs: numpy.array
            single-cell matrix
            
        perturb_us: numpy.array
            perturbation information for cells

        soft_assign: bool
            use similarity to all codebook items for prediction or rely on the information
            from the most similar codebook item.
            
        batch_size: int
            size of batch processing
            
        show_progress: bool
            verbose on or off
        """
        #xs = self.preprocess(xs)
        if (self.specific_mode == 'codebook'):
            zs = self.codebook_map(xs, soft_assign=soft_assign, show_progress=show_progress)
        else:
            zs = self.get_basal_embedding(xs, show_progress=show_progress)
        zs = convert_to_tensor(zs, device='cpu')
        ps = convert_to_tensor(perturb_us, device='cpu')
        ts = convert_to_tensor(perturb_type, device='cpu')
        dataset = CustomDataset(zs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for Z_batch, idx in dataloader:
                Z_batch = Z_batch.to(self.get_device())
                P_batch = ps[idx].to(self.get_device())
                T_batch = ts[idx].to(self.get_device())
                zns = self._cell_shift(Z_batch, P_batch, T_batch)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z
    
    def _log_mu(self, zs):
        return self.decoder_log_mu(zs)
    
    def get_log_mu(self, zs, batch_size: int = 1024, show_progress=True):
        """
        Return cells' changes in the feature space induced by specific perturbation of a factor

        """
        zs = convert_to_tensor(zs, device='cpu')
        dataset = CustomDataset(zs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        R = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for Z_batch, _ in dataloader:
                Z_batch = Z_batch.to(self.get_device())
                r = self._log_mu(Z_batch)
                R.append(tensor_to_numpy(r))
                pbar.update(1)

        R = np.concatenate(R)
        return R
    
    def _count(self, log_mu, library_size=None):
        if self.loss_func == 'bernoulli':
            counts = dist.Bernoulli(logits=log_mu).to_event(1).mean
        elif self.loss_func == 'negbinomial':
            counts = log_mu.exp()
        else:
            rate = log_mu.exp()
            theta = dist.DirichletMultinomial(total_count=1, concentration=rate).mean
            counts = theta * library_size
        return counts
    
    def get_counts(self, zs, library_sizes, batch_size: int = 1024, show_progress=True):
        '''
        Generate observational profiles from latent states.
        
        Parameters
        ----------
        zs: numpy.array
            latent states for cells
            
        library_sizes: numpy.array
            library sizes for cells
            
        batch_size: int
            size of batch processing
            
        show_progress: bool
            verbose on or off
        '''

        zs = convert_to_tensor(zs, device=self.get_device())
        
        if type(library_sizes) == list:
            library_sizes = np.array(library_sizes).reshape(-1,1)
        elif len(library_sizes.shape)==1:
            library_sizes = library_sizes.reshape(-1,1)
        ls = convert_to_tensor(library_sizes, device='cpu')
        
        dataset = CustomDataset(zs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
        
        E = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for Z_batch, idx in dataloader:
                Z_batch = Z_batch.to(self.get_device())
                L_batch = ls[idx].to(self.get_device())
                log_mu = self._log_mu(Z_batch)
                counts = self._count(log_mu, L_batch)
                E.append(tensor_to_numpy(counts))
                pbar.update(1)
        
        E = np.concatenate(E)
        return E
    
    def preprocess(self, xs, threshold=0):
        if self.loss_func == 'bernoulli':
            ad = sc.AnnData(xs)
            binarize(ad, threshold=threshold)
            xs = ad.X.copy()
        elif self.loss_func in ['poisson','multinomial']:
            xs = np.round(xs)
        elif self.specific_mode=='codebook': # negbinomial
            xs = np.round(xs)
            
        if sparse.issparse(xs):
            xs = xs.toarray()
        return xs 
    
    def fit(self, xs, 
            us = None, 
            ts = None,
            cs = None,
            num_epochs: int = 100, 
            learning_rate: float = 0.0001, 
            batch_size: int = 256, 
            algo: Literal['adam','rmsprop','adamw'] = 'adam', 
            beta_1: float = 0.9, 
            weight_decay: float = 0.005, 
            decay_rate: float = 0.9,
            config_enum: str = 'parallel',
            threshold: int = 0,
            use_jax: bool = False,
            show_progress=True):
        """
        Train the DensityFlowNSF model.

        Parameters
        ----------
        xs: numpy.array
            Single-cell experssion matrix. It should be a Numpy array or a Pytorch Tensor. Rows are cells and columns are features.
        us: numpy.array
            cell-level factor matrix. 
        num_epochs: int
            Number of training epochs.
        learning_rate: float
            Parameter for training.
        batch_size: int
            Size of batch processing.
        algo: str
            Optimization algorithm.
        beta_1: float
            Parameter for optimization.
        weight_decay: float
            Parameter for optimization.
        decay_rate: float
            Parameter for optimization.
        use_jax: bool
            If toggled on, Jax will be used for speeding up. CAUTION: This will raise errors because of unknown reasons when it is called in
            the Python script or Jupyter notebook. It is OK if it is used when runing DensityFlowNSF in the shell command.
        show_progress: bool
            verbose on or off
        """
        xs = self.preprocess(xs, threshold=threshold)
        xs = convert_to_tensor(xs, dtype=self.dtype, device='cpu')
        if us is not None:
            us = convert_to_tensor(us, dtype=self.dtype, device='cpu')
            ts = convert_to_tensor(ts, dtype=self.dtype, device='cpu')
        if cs is not None:
            cs = convert_to_tensor(cs, dtype=self.dtype, device='cpu')

        dataset = CustomDataset(xs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        # setup the optimizer
        optim_params = {'lr': learning_rate, 'betas': (beta_1, 0.999), 'weight_decay': weight_decay}

        if algo.lower()=='rmsprop':
            optimizer = torch.optim.RMSprop
        elif algo.lower()=='adam':
            optimizer = torch.optim.Adam
        elif algo.lower() == 'adamw':
            optimizer = torch.optim.AdamW
        else:
            raise ValueError("An optimization algorithm must be specified.")
        scheduler = ExponentialLR({'optimizer': optimizer, 'optim_args': optim_params, 'gamma': decay_rate})

        pyro.clear_param_store()

        # set up the loss(es) for inference, wrapping the guide in config_enumerate builds the loss as a sum
        # by enumerating each class label form the sampled discrete categorical distribution in the model
        Elbo = JitTraceEnum_ELBO if use_jax else TraceEnum_ELBO
        elbo = Elbo(max_plate_nesting=1, strict_enumeration_warning=False)
        guide = config_enumerate(self.guide, config_enum, expand=True)
        loss_basic = SVI(self.model, guide, scheduler, loss=elbo)

        # build a list of all losses considered
        losses = [loss_basic]
        num_losses = len(losses)

        with tqdm(total=num_epochs, disable=not show_progress, desc='Training', unit='epoch') as pbar:
            for epoch in range(num_epochs):
                epoch_losses = [0.0] * num_losses
                for batch_x, idx in dataloader:
                    batch_x = batch_x.to(self.get_device())
                    batch_u,batch_t,batch_c = None,None,None
                    if us is not None:
                        batch_u = us[idx].to(self.get_device())
                        batch_t = ts[idx].to(self.get_device())
                    if cs is not None:
                        batch_c = cs[idx].to(self.get_device())

                    for loss_id in range(num_losses):
                        new_loss = losses[loss_id].step(batch_x, us=batch_u, ts=batch_t, cs=batch_c)
                        epoch_losses[loss_id] += new_loss

                avg_epoch_losses_ = map(lambda v: v / len(dataloader), epoch_losses)
                avg_epoch_losses = map(lambda v: "{:.4f}".format(v), avg_epoch_losses_)

                # store the loss
                str_loss = " ".join(map(str, avg_epoch_losses))

                # Update progress bar
                pbar.set_postfix({'loss': str_loss})
                pbar.update(1)
                
    @classmethod
    def save_model(cls, model, file_path, compression=False):
        """Save the model to the specified file path."""
        file_path = os.path.abspath(file_path)

        model.eval()
        if compression:
            with gzip.open(file_path, 'wb') as pickle_file:
                pickle.dump(model, pickle_file)
        else:
            with open(file_path, 'wb') as pickle_file:
                pickle.dump(model, pickle_file)

        print(f'Model saved to {file_path}')

    @classmethod
    def load_model(cls, file_path):
        """Load the model from the specified file path and return an instance."""
        print(f'Model loaded from {file_path}')

        file_path = os.path.abspath(file_path)
        if file_path.endswith('gz'):
            with gzip.open(file_path, 'rb') as pickle_file:
                model = pickle.load(pickle_file)
        else:
            with open(file_path, 'rb') as pickle_file:
                model = pickle.load(pickle_file)
                
        print(f"🧬 DensityFlowNSF Initialized:")
        print(f"   - Codebook size: {model.code_dim}")
        print(f"   - Latent Dimension: {model.latent_dim}")
        print(f"   - Gene Dimension: {model.input_dim}")
        print(f"   - Hidden Dimensions: {model.hidden_layers}")
        print(f"   - Device: {model.get_device()}")
        print(f"   - Parameters: {sum(p.numel() for p in model.parameters()):,}")
        
        return model
        
'''    def save(self, path):
        """Save model checkpoint"""
        torch.save({
            'model_state_dict': self.state_dict(),
            'model_config': {
                'input_dim': self.input_dim,
                'codebook_size': self.code_dim,
                'perturb_size': self.perturb_size,
                'specific_mode':self.specific_mode,
                'z_dim': self.latent_dim,
                'z_dist': self.latent_dist,
                'loss_func': self.loss_func,
                'dispersion': self.dispersion,
                'use_zeroinflate': self.use_zeroinflate,
                'hidden_layers':self.hidden_layers,
                'hidden_layer_activation':self.hidden_layer_activation,
                'nn_dropout':self.nn_dropout,
                'post_layer_fct':self.post_layer_fct,
                'post_act_fct':self.post_act_fct,
                'config_enum':self.config_enum,
                'use_cuda':self.use_cuda,
                'seed':self.seed,
                'zero_bias':self.use_bias,
                'dtype':self.dtype,
            }
        }, path)
    
    @classmethod
    def load_model(cls, model_path: str):
        """Load pre-trained model"""
        checkpoint = torch.load(model_path)
        model = DensityFlowNSF(**checkpoint.get('model_config'))
        
        checkpoint = torch.load(model_path, map_location=model.get_device())
        model.load_state_dict(checkpoint['model_state_dict'])
        
        return model'''

        
EXAMPLE_RUN = (
    "example run: DensityFlowNSF --help"
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="DensityFlowNSF\n{}".format(EXAMPLE_RUN))

    parser.add_argument(
        "--cuda", action="store_true", help="use GPU(s) to speed up training"
    )
    parser.add_argument(
        "--jit", action="store_true", help="use PyTorch jit to speed up training"
    )
    parser.add_argument(
        "-n", "--num-epochs", default=200, type=int, help="number of epochs to run"
    )
    parser.add_argument(
        "-enum",
        "--enum-discrete",
        default="parallel",
        help="parallel, sequential or none. uses parallel enumeration by default",
    )
    parser.add_argument(
        "-data",
        "--data-file",
        default=None,
        type=str,
        help="the data file",
    )
    parser.add_argument(
        "-cf",
        "--cell-factor-file",
        default=None,
        type=str,
        help="the file for the record of cell-level factors",
    )
    parser.add_argument(
        "-bs",
        "--batch-size",
        default=1000,
        type=int,
        help="number of cells to be considered in a batch",
    )
    parser.add_argument(
        "-lr",
        "--learning-rate",
        default=0.0001,
        type=float,
        help="learning rate for Adam optimizer",
    )
    parser.add_argument(
        "-cs",
        "--codebook-size",
        default=100,
        type=int,
        help="size of vector quantization codebook",
    )
    parser.add_argument(
        "--z-dist",
        default='gumbel',
        type=str,
        choices=['normal','laplacian','studentt','gumbel','cauchy'],
        help="distribution model for latent representation",
    )
    parser.add_argument(
        "-zd",
        "--z-dim",
        default=10,
        type=int,
        help="size of the tensor representing the latent variable z variable",
    )
    parser.add_argument(
        "-likeli",
        "--likelihood",
        default='negbinomial',
        type=str,
        choices=['negbinomial', 'multinomial', 'poisson', 'bernoulli'],
        help="specify the distribution likelihood function",
    )
    parser.add_argument(
        "-zi",
        "--zeroinflate",
        action="store_true",
        help="use zero-inflated estimation",
    )
    parser.add_argument(
        "-id",
        "--inverse-dispersion",
        default=10.0,
        type=float,
        help="inverse dispersion prior for negative binomial",
    )
    parser.add_argument(
        "-hl",
        "--hidden-layers",
        nargs="+",
        default=[500],
        type=int,
        help="a tuple (or list) of MLP layers to be used in the neural networks "
        "representing the parameters of the distributions in our model",
    )
    parser.add_argument(
        "-hla",
        "--hidden-layer-activation",
        default='relu',
        type=str,
        choices=['relu','softplus','leakyrelu','linear'],
        help="activation function for hidden layers",
    )
    parser.add_argument(
        "-plf",
        "--post-layer-function",
        nargs="+",
        default=['layernorm'],
        type=str,
        help="post functions for hidden layers, could be none, dropout, layernorm, batchnorm, or combination, default is 'dropout layernorm'",
    )
    parser.add_argument(
        "-paf",
        "--post-activation-function",
        nargs="+",
        default=['none'],
        type=str,
        help="post functions for activation layers, could be none or dropout, default is 'none'",
    )
    parser.add_argument(
        "-64",
        "--float64",
        action="store_true",
        help="use double float precision",
    )
    parser.add_argument(
        "-dr",
        "--decay-rate",
        default=0.9,
        type=float,
        help="decay rate for Adam optimizer",
    )
    parser.add_argument(
        "--layer-dropout-rate",
        default=0.1,
        type=float,
        help="droput rate for neural networks",
    )
    parser.add_argument(
        "-b1",
        "--beta-1",
        default=0.95,
        type=float,
        help="beta-1 parameter for Adam optimizer",
    )  
    parser.add_argument(
        "--seed",
        default=None,
        type=int,
        help="seed for controlling randomness in this example",
    )
    parser.add_argument(
        "--save-model",
        default=None,
        type=str,
        help="path to save model for prediction",
    )
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    assert (
        (args.data_file is not None) and (
            os.path.exists(args.data_file))
    ), "data file must be provided"

    if args.seed is not None:
        set_random_seed(args.seed)

    if args.float64:
        dtype = torch.float64
        torch.set_default_dtype(torch.float64)
    else:
        dtype = torch.float32
        torch.set_default_dtype(torch.float32)

    xs = dt.fread(file=args.data_file, header=True).to_numpy()
    us = None 
    if args.cell_factor_file is not None:
        us = dt.fread(file=args.cell_factor_file, header=True).to_numpy()

    input_dim = xs.shape[1]
    perturb_size = 0 if us is None else us.shape[1]

    ###########################################
    df = DensityFlowNSF(
        input_dim=input_dim,
        perturb_size=perturb_size,
        dispersion=args.dispersion,
        z_dim=args.z_dim,
        hidden_layers=args.hidden_layers,
        hidden_layer_activation=args.hidden_layer_activation,
        use_cuda=args.cuda,
        config_enum=args.enum_discrete,
        use_zeroinflate=args.zeroinflate,
        loss_func=args.likelihood,
        nn_dropout=args.layer_dropout_rate,
        post_layer_fct=args.post_layer_function,
        post_act_fct=args.post_activation_function,
        codebook_size=args.codebook_size,
        z_dist = args.z_dist,
        dtype=dtype,
    )

    df.fit(xs, us=us, 
             num_epochs=args.num_epochs,
             learning_rate=args.learning_rate,
             batch_size=args.batch_size,
             beta_1=args.beta_1,
             decay_rate=args.decay_rate,
             use_jax=args.jit,
             config_enum=args.enum_discrete,
             )

    if args.save_model is not None:
        if args.save_model.endswith('gz'):
            DensityFlowNSF.save_model(df, args.save_model, compression=True)
        else:
            DensityFlowNSF.save_model(df, args.save_model)
    


if __name__ == "__main__":
    main()