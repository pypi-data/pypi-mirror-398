import pyro
import pyro.distributions as dist
from pyro.optim import ExponentialLR
from pyro.infer import SVI, JitTraceEnum_ELBO, TraceEnum_ELBO, config_enumerate

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

class DensityFlowMO2(nn.Module):
    """DensityFlowMO2 model

    Parameters
    ----------
    input_size : int
        Number of features like genes or peaks

    codebook_size: int
        Number of codebook items

    perturb_size: int
        Number of perturbations 
        
    cov_size: int
        Number of covariates

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
    >>> from DensityFlowMO2 import DensityFlowMO2
    >>> from DensityFlowMO2.perturb import LabelMatrix
    >>> import scanpy as sc
    >>> adata = sc.read('dataset.h5ad')
    >>> adata.X = adata.layers['counts].copy()
    >>> sc.pp.normalize_total(adata)
    >>> sc.pp.log1p(adata)
    >>> xs = adata.X 
    >>> lb = LabelMatrix()
    >>> us = lb.fit_transform(adata_train.obs[pert_col], control_label=control_label)
    >>> ln = lb.labels_
    >>> model = DensityFlowMO2(input_size = xs.shape[1],
                            perturb_size=us.shape[1],
                            use_cuda=True)
    >>> model.fit(xs, us=us, use_jax=True)
    >>> zs_basal = model.get_basal_embedding(xs)
    >>> zs_complete = model.get_complete_embedding(xs, us)
    """
    def __init__(self,
                 rna_dim: int,
                 atac_dim: int,
                 codebook_size: int = 15,
                 perturb_size: int = 0,
                 cov_size: int = 0,
                 transforms: int = 3,
                 z_dim: int = 50,
                 z_dist: Literal['normal','studentt','laplacian','cauchy','gumbel'] = 'studentt',
                 rna_loss_func: Literal['negbinomial','poisson','multinomial','bernoulli'] = 'negbinomial',
                 atac_loss_func: Literal['negbinomial','poisson','multinomial','bernoulli'] = 'multinomial',
                 dispersion: float = 10.0,
                 use_zeroinflate: bool = False,
                 hidden_layers: list = [512],
                 hidden_layer_activation: Literal['relu','softplus','leakyrelu','linear'] = 'relu',
                 flow_hidden_layers: list = [128,128],
                 nn_dropout: float = 0.1,
                 post_layer_fct: list = ['layernorm'],
                 post_act_fct: list = None,
                 config_enum: str = 'parallel',
                 use_cuda: bool = True,
                 seed: int = 42,
                 dtype = torch.float32, # type: ignore
                 ):
        super().__init__()

        self.rna_dim = rna_dim
        self.atac_dim = atac_dim
        self.perturb_size = perturb_size
        self.cov_size = cov_size
        self.dispersion = dispersion
        self.latent_dim = z_dim
        self.hidden_layers = hidden_layers
        self.decoder_hidden_layers = hidden_layers[::-1]
        self.config_enum = config_enum
        self.allow_broadcast = config_enum == 'parallel'
        self.use_cuda = use_cuda
        self.rna_loss_func = rna_loss_func
        self.atac_loss_func = atac_loss_func
        self.options = None
        self.code_size=codebook_size
        self.latent_dist = z_dist
        self.dtype = dtype
        self.use_zeroinflate=use_zeroinflate
        self.nn_dropout = nn_dropout
        self.post_layer_fct = post_layer_fct
        self.post_act_fct = post_act_fct
        self.hidden_layer_activation = hidden_layer_activation
        self.transforms = transforms
        self.flow_hidden_layers = flow_hidden_layers
        
        self.codebook_weights = None

        self.seed = seed
        set_random_seed(seed)
        self.setup_networks()
        
        print(f"🧬 DensityFlowMO2 Initialized:")
        print(f"   - Codebook size: {self.code_size}")
        print(f"   - Latent Dimension: {self.latent_dim}")
        print(f"   - Gene Dimension: {self.rna_dim}")
        print(f"   - ATAC Dimension: {self.atac_dim}")
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

        self.encoder_rna_n = MLP(
                [self.latent_dim] + hidden_sizes + [self.code_size],
                activation=activate_fct,
                output_activation=None,
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )

        self.encoder_atac_n = MLP(
                [self.latent_dim] + hidden_sizes + [self.code_size],
                activation=activate_fct,
                output_activation=None,
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )
        
        self.encoder_rna_zn = MLP(
            [self.rna_dim] + hidden_sizes + [[latent_dim, latent_dim]],
            activation=activate_fct,
            output_activation=[None, Exp],
            post_layer_fct=post_layer_fct,
            post_act_fct=post_act_fct,
            allow_broadcast=self.allow_broadcast,
            use_cuda=self.use_cuda,
        )
        
        self.encoder_atac_zn = MLP(
            [self.atac_dim] + hidden_sizes + [[latent_dim, latent_dim]],
            activation=activate_fct,
            output_activation=[None, Exp],
            post_layer_fct=post_layer_fct,
            post_act_fct=post_act_fct,
            allow_broadcast=self.allow_broadcast,
            use_cuda=self.use_cuda,
        )

        if self.cov_size>0:
            self.covariate_rna_effect = ZeroBiasMLP2(
                [self.cov_size] + self.decoder_hidden_layers + [self.latent_dim],
                activation=activate_fct,
                output_activation=None,
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )
            self.covariate_atac_effect = ZeroBiasMLP2(
                [self.cov_size] + self.decoder_hidden_layers + [self.latent_dim],
                activation=activate_fct,
                output_activation=None,
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )
            
        if self.perturb_size>0:
            self.perturb_rna_effect = ZeroBiasMLP3(
                    [self.perturb_size+self.latent_dim] + self.decoder_hidden_layers + [self.latent_dim],
                    activation=activate_fct,
                    output_activation=None,
                    post_layer_fct=post_layer_fct,
                    post_act_fct=post_act_fct,
                    allow_broadcast=self.allow_broadcast,
                    use_cuda=self.use_cuda,
                )
            
            self.perturb_atac_effect = ZeroBiasMLP3(
                    [self.perturb_size+self.latent_dim] + self.decoder_hidden_layers + [self.latent_dim],
                    activation=activate_fct,
                    output_activation=None,
                    post_layer_fct=post_layer_fct,
                    post_act_fct=post_act_fct,
                    allow_broadcast=self.allow_broadcast,
                    use_cuda=self.use_cuda,
                )
             
        self.decoder_atac2rna = MLP(
                    [self.code_size] + self.decoder_hidden_layers + [self.code_size],
                    activation=activate_fct,
                    output_activation=None,
                    post_layer_fct=post_layer_fct,
                    post_act_fct=post_act_fct,
                    allow_broadcast=self.allow_broadcast,
                    use_cuda=self.use_cuda,
                )
        self.decoder_rna2atac = MLP(
                    [self.code_size] + self.decoder_hidden_layers + [self.code_size],
                    activation=activate_fct,
                    output_activation=None,
                    post_layer_fct=post_layer_fct,
                    post_act_fct=post_act_fct,
                    allow_broadcast=self.allow_broadcast,
                    use_cuda=self.use_cuda,
                )
            
        self.decoder_rna_log_mu = MLP(
                    [self.latent_dim] + self.decoder_hidden_layers + [self.rna_dim],
                    activation=activate_fct,
                    output_activation=None,
                    post_layer_fct=post_layer_fct,
                    post_act_fct=post_act_fct,
                    allow_broadcast=self.allow_broadcast,
                    use_cuda=self.use_cuda,
                )
        self.decoder_atac_log_mu = MLP(
                    [self.latent_dim] + self.decoder_hidden_layers + [self.atac_dim],
                    activation=activate_fct,
                    output_activation=None,
                    post_layer_fct=post_layer_fct,
                    post_act_fct=post_act_fct,
                    allow_broadcast=self.allow_broadcast,
                    use_cuda=self.use_cuda,
                )

        if self.latent_dist == 'studentt':
            self.rna_codebook = MLP(
                [self.code_size] + hidden_sizes + [[latent_dim,latent_dim]],
                activation=activate_fct,
                output_activation=[Exp,None],
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )
            self.atac_codebook = MLP(
                [self.code_size] + hidden_sizes + [[latent_dim,latent_dim]],
                activation=activate_fct,
                output_activation=[Exp,None],
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )
        else:
            self.rna_codebook = MLP(
                [self.code_size] + hidden_sizes + [latent_dim],
                activation=activate_fct,
                output_activation=None,
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )
            self.atac_codebook = MLP(
                [self.code_size] + hidden_sizes + [latent_dim],
                activation=activate_fct,
                output_activation=None,
                post_layer_fct=post_layer_fct,
                post_act_fct=post_act_fct,
                allow_broadcast=self.allow_broadcast,
                use_cuda=self.use_cuda,
            )
        
        
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

    def rna_model(self, xs_rna, us=None, cs=None):
        pyro.module('DensityFlowMO2', self)

        batch_size = xs_rna.size(0)
        self.options = dict(dtype=xs_rna.dtype, device=xs_rna.device)
        
        if self.rna_loss_func=='negbinomial':
            rna_dispersion = pyro.param("rna_dispersion", self.dispersion *
                                            xs_rna.new_ones(self.rna_dim), constraint=constraints.positive)
            
        if self.use_zeroinflate:
            rna_gate_logits = pyro.param("rna_dropout_rate", xs_rna.new_zeros(self.rna_dim))
            
        rna_acs_scale = pyro.param("rna_codebook_scale", xs_rna.new_ones(self.latent_dim), constraint=constraints.positive)

        I = torch.eye(self.code_size)
        if self.latent_dist=='studentt':
            rna_acs_dof,rna_acs_loc = self.rna_codebook(I)
        else:
            rna_acs_loc = self.rna_codebook(I)
            
        with pyro.plate('data'):
            ###############################################################
            # RNA 
            prior = torch.zeros(batch_size, self.code_size, **self.options)
            ns = pyro.sample('rna_n', dist.OneHotCategorical(logits=prior))

            zn_loc = torch.matmul(ns,rna_acs_loc)
            #zn_scale = torch.matmul(ns,acs_scale)
            zn_scale = rna_acs_scale

            if self.latent_dist == 'studentt':
                prior_dof = torch.matmul(ns,rna_acs_dof)
                rna_zns = pyro.sample('rna_zn', dist.StudentT(df=prior_dof, loc=zn_loc, scale=zn_scale).to_event(1))
            elif self.latent_dist == 'laplacian':
                rna_zns = pyro.sample('rna_zn', dist.Laplace(zn_loc, zn_scale).to_event(1))
            elif self.latent_dist == 'cauchy':
                rna_zns = pyro.sample('rna_zn', dist.Cauchy(zn_loc, zn_scale).to_event(1))
            elif self.latent_dist == 'normal':
                rna_zns = pyro.sample('rna_zn', dist.Normal(zn_loc, zn_scale).to_event(1))
            elif self.latent_dist == 'gumbel':
                rna_zns = pyro.sample('rna_zn', dist.Gumbel(zn_loc, zn_scale).to_event(1))

            rna_zs = rna_zns
            if self.perturb_size>0:
                rna_zus = self._total_rna_effects(rna_zns, us)
                rna_zs = rna_zs+rna_zus
                
            if self.cov_size>0:
                rna_zcs = self.covariate_rna_effect(cs)
                rna_zs = rna_zs + rna_zcs

            rna_log_mu = self.decoder_rna_log_mu(rna_zs)
            if self.rna_loss_func in ['bernoulli']:
                rna_log_theta = rna_log_mu
            elif self.rna_loss_func == 'negbinomial':
                rna_mu = rna_log_mu.exp()
                
                #dispersion = self.decoder_dispersion(zs)
                #dispersion = dispersion.exp()
            else:
                rna_rate = rna_log_mu.exp()
                rna_theta = dist.DirichletMultinomial(total_count=1, concentration=rna_rate).mean
                if self.rna_loss_func == 'poisson':
                    rna_rate = rna_theta * torch.sum(xs_rna, dim=1, keepdim=True)

            if self.rna_loss_func == 'negbinomial':
                if self.use_zeroinflate:
                    pyro.sample("rna_x", MyZINB(mu=rna_mu, theta=rna_dispersion, zi_logits=rna_gate_logits).to_event(1), obs=xs_rna)
                else:
                    pyro.sample("rna_x", MyNB(mu=rna_mu, theta=rna_dispersion).to_event(1), obs=xs_rna)
            elif self.rna_loss_func == 'poisson':
                if self.use_zeroinflate:
                    pyro.sample('rna_x', dist.ZeroInflatedDistribution(dist.Poisson(rate=rna_rate),gate_logits=rna_gate_logits).to_event(1), obs=xs_rna.round())
                else:
                    pyro.sample('rna_x', dist.Poisson(rate=rna_rate).to_event(1), obs=xs_rna.round())
            elif self.rna_loss_func == 'multinomial':
                pyro.sample('rna_x', dist.Multinomial(total_count=int(1e8), probs=rna_theta), obs=xs_rna)
            elif self.rna_loss_func == 'bernoulli':
                if self.use_zeroinflate:
                    pyro.sample('rna_x', dist.ZeroInflatedDistribution(dist.Bernoulli(logits=rna_log_theta),gate_logits=rna_gate_logits).to_event(1), obs=xs_rna)
                else:
                    pyro.sample('rna_x', dist.Bernoulli(logits=rna_log_theta).to_event(1), obs=xs_rna)
                    
    def rna_guide(self, xs_rna, us=None, cs=None):
        with pyro.plate('data'):
            # RNA
            zn_loc, zn_scale = self._get_rna_basal_embedding(xs_rna)
            zns = pyro.sample('rna_zn', dist.Normal(zn_loc, zn_scale).to_event(1))

            alpha = self.encoder_rna_n(zns)
            ns = pyro.sample('rna_n', dist.OneHotCategorical(logits=alpha))
    
    def atac_model(self, xs_atac, us=None, cs=None):
        pyro.module('DensityFlowMO2', self)

        batch_size = xs_atac.size(0)
        
        if self.atac_loss_func=='negbinomial':
            atac_dispersion = pyro.param("atac_dispersion", self.dispersion *
                                            xs_atac.new_ones(self.atac_dim), constraint=constraints.positive)
            
        if self.use_zeroinflate:
            atac_gate_logits = pyro.param("atac_dropout_rate", xs_atac.new_zeros(self.atac_dim))
            
        atac_acs_scale = pyro.param("atac_codebook_scale", xs_atac.new_ones(self.latent_dim), constraint=constraints.positive)

        I = torch.eye(self.code_size)
        if self.latent_dist=='studentt':
            atac_acs_dof,atac_acs_loc = self.atac_codebook(I)
        else:
            atac_acs_loc = self.atac_codebook(I)
            
        with pyro.plate('data'):
            ###############################################################
            # atac 
            prior = torch.zeros(batch_size, self.code_size, **self.options)
            ns = pyro.sample('atac_n', dist.OneHotCategorical(logits=prior))

            zn_loc = torch.matmul(ns,atac_acs_loc)
            #zn_scale = torch.matmul(ns,acs_scale)
            zn_scale = atac_acs_scale

            if self.latent_dist == 'studentt':
                prior_dof = torch.matmul(ns,atac_acs_dof)
                atac_zns = pyro.sample('atac_zn', dist.StudentT(df=prior_dof, loc=zn_loc, scale=zn_scale).to_event(1))
            elif self.latent_dist == 'laplacian':
                atac_zns = pyro.sample('atac_zn', dist.Laplace(zn_loc, zn_scale).to_event(1))
            elif self.latent_dist == 'cauchy':
                atac_zns = pyro.sample('atac_zn', dist.Cauchy(zn_loc, zn_scale).to_event(1))
            elif self.latent_dist == 'normal':
                atac_zns = pyro.sample('atac_zn', dist.Normal(zn_loc, zn_scale).to_event(1))
            elif self.latent_dist == 'gumbel':
                atac_zns = pyro.sample('atac_zn', dist.Gumbel(zn_loc, zn_scale).to_event(1))

            atac_zs = atac_zns
            if self.perturb_size>0:
                atac_zus = self._total_atac_effects(atac_zns, us)
                atac_zs = atac_zs+atac_zus
                
            if self.cov_size>0:
                atac_zcs = self.covariate_atac_effect(cs)
                atac_zs = atac_zs + atac_zcs

            atac_log_mu = self.decoder_atac_log_mu(atac_zs)
            if self.atac_loss_func in ['bernoulli']:
                atac_log_theta = atac_log_mu
            elif self.atac_loss_func == 'negbinomial':
                atac_mu = atac_log_mu.exp()
                
                #dispersion = self.decoder_dispersion(zs)
                #dispersion = dispersion.exp()
            else:
                atac_rate = atac_log_mu.exp()
                atac_theta = dist.DirichletMultinomial(total_count=1, concentration=atac_rate).mean
                if self.atac_loss_func == 'poisson':
                    atac_rate = atac_theta * torch.sum(xs_atac, dim=1, keepdim=True)

            if self.atac_loss_func == 'negbinomial':
                if self.use_zeroinflate:
                    pyro.sample("atac_x", MyZINB(mu=atac_mu, theta=atac_dispersion, zi_logits=atac_gate_logits).to_event(1), obs=xs_atac)
                else:
                    pyro.sample("atac_x", MyNB(mu=atac_mu, theta=atac_dispersion).to_event(1), obs=xs_atac)
            elif self.atac_loss_func == 'poisson':
                if self.use_zeroinflate:
                    pyro.sample('atac_x', dist.ZeroInflatedDistribution(dist.Poisson(rate=atac_rate),gate_logits=atac_gate_logits).to_event(1), obs=xs_atac.round())
                else:
                    pyro.sample('atac_x', dist.Poisson(rate=atac_rate).to_event(1), obs=xs_atac.round())
            elif self.atac_loss_func == 'multinomial':
                pyro.sample('atac_x', dist.Multinomial(total_count=int(1e8), probs=atac_theta), obs=xs_atac)
            elif self.atac_loss_func == 'bernoulli':
                if self.use_zeroinflate:
                    pyro.sample('atac_x', dist.ZeroInflatedDistribution(dist.Bernoulli(logits=atac_log_theta),gate_logits=atac_gate_logits).to_event(1), obs=xs_atac)
                else:
                    pyro.sample('atac_x', dist.Bernoulli(logits=atac_log_theta).to_event(1), obs=xs_atac)

    def atac_guide(self, xs_atac, us=None, cs=None):
        with pyro.plate('data'):
            # ATAC
            zn_loc, zn_scale = self._get_atac_basal_embedding(xs_atac)
            zns = pyro.sample('atac_zn', dist.Normal(zn_loc, zn_scale).to_event(1))

            alpha = self.encoder_atac_n(zns)
            ns = pyro.sample('atac_n', dist.OneHotCategorical(logits=alpha))
            
    def cross_model(self, rna_ns_logits, atac_ns_logits):
        pyro.module('DensityFlowMO2', self)

        with pyro.plate('data'):
            res, ind = torch.topk(rna_ns_logits, 1)
            rna_ns = torch.zeros_like(rna_ns_logits).scatter_(1, ind, 1.0)
            
            res, ind = torch.topk(atac_ns_logits, 1)
            atac_ns = torch.zeros_like(atac_ns_logits).scatter_(1, ind, 1.0)
            ###############################################################
            # RNA 
            rna_logits = self.decoder_atac2rna(atac_ns_logits)
            _ = pyro.sample('atac2rna_ns', dist.OneHotCategorical(logits=rna_logits), obs=rna_ns)

            ###############################################################
            # atac 
            atac_logits = self.decoder_rna2atac(rna_ns_logits)
            _ = pyro.sample('rna2atac_zns', dist.OneHotCategorical(logits=atac_logits), obs=atac_ns)
                    
    def cross_guide(self, rna_ns_logits, atac_ns_logits):
        pass
    
    def _total_rna_effects(self, rna_zs, us):
        zus = self._rna_cell_shift(rna_zs, us)
        return zus
    
    def _total_atac_effects(self, atac_zs, us):
        zus = self._atac_cell_shift(atac_zs, us)
        return zus
                        
    def _get_codebook_identity(self):
        return torch.eye(self.code_size, **self.options)
    
    def _get_rna_codebook(self):
        I = torch.eye(self.code_size, **self.options)
        if self.latent_dist=='studentt':
            _,cb = self.rna_codebook(I)
        else:
            cb = self.rna_codebook(I)
        return cb
    
    def get_rna_codebook(self):
        """
        Return the mean part of metacell codebook
        """
        cb = self._get_rna_codebook()
        cb = tensor_to_numpy(cb)
        return cb

    def _rna_codebook_map(self, xs_rna, soft_assign):
        if soft_assign:
            ns = self._rna_soft_assignments(xs_rna)
        else:
            ns = self._rna_hard_assignments(xs_rna)
        cb = self._get_rna_codebook()
        zs = torch.matmul(ns, cb)
        return zs
    
    def rna_codebook_map(self, xs_rna, soft_assign: bool=True, batch_size:int=1024, show_progress=True):
        xs_rna = self.preprocess(xs_rna,'rna')
        xs_rna = convert_to_tensor(xs_rna, device='cpu')
        dataset = CustomDataset(xs_rna)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                zns = self._rna_codebook_map(X_batch, soft_assign)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z
    
    def _get_atac_codebook(self):
        I = torch.eye(self.code_size, **self.options)
        if self.latent_dist=='studentt':
            _,cb = self.atac_codebook(I)
        else:
            cb = self.atac_codebook(I)
        return cb
    
    def get_atac_codebook(self):
        """
        Return the mean part of metacell codebook
        """
        cb = self._get_atac_codebook()
        cb = tensor_to_numpy(cb)
        return cb

    def _atac_codebook_map(self, xs_atac, soft_assign):
        if soft_assign:
            ns = self._atac_soft_assignments(xs_atac)
        else:
            ns = self._atac_hard_assignments(xs_atac)
        cb = self._get_rna_codebook()
        zs = torch.matmul(ns, cb)
        return zs
    
    def atac_codebook_map(self, xs_atac, soft_assign: bool=True, batch_size:int=1024, show_progress=True):
        xs_atac = self.preprocess(xs_atac,'atac')
        xs_atac = convert_to_tensor(xs_atac, device='cpu')
        dataset = CustomDataset(xs_atac)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                zns = self._atac_codebook_map(X_batch, soft_assign)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z
    
    def _get_rna_complete_embedding(self, xs_rna, us):
        basal,_ = self._get_rna_basal_embedding(xs_rna)
        dzs = self._total_rna_effects(basal, us)
        return basal + dzs 
    
    def get_rna_complete_embedding(self, xs_rna, us, batch_size:int=1024, show_progress=True):
        xs_rna = self.preprocess(xs_rna,'rna')
        xs_rna = convert_to_tensor(xs_rna, device='cpu')
        us = convert_to_tensor(us, device='cpu')
        dataset = CustomDataset(xs_rna)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, idx in dataloader:
                X_batch = X_batch.to(self.get_device())
                U_batch = us[idx].to(self.get_device())
                zns = self._get_rna_complete_embedding(X_batch, U_batch)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z
    
    def _get_atac_complete_embedding(self, xs_atac, us):
        basal,_ = self._get_atac_basal_embedding(xs_atac)
        dzs = self._total_atac_effects(basal, us)
        return basal + dzs 
    
    def get_atac_complete_embedding(self, xs_atac, us, batch_size:int=1024, show_progress=True):
        xs_atac = self.preprocess(xs_atac,'atac')
        xs_atac = convert_to_tensor(xs_atac, device='cpu')
        us = convert_to_tensor(us, device='cpu')
        dataset = CustomDataset(xs_atac)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, idx in dataloader:
                X_batch = X_batch.to(self.get_device())
                U_batch = us[idx].to(self.get_device())
                zns = self._get_atac_complete_embedding(X_batch, U_batch)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z

    def _get_rna_basal_embedding(self, xs_rna):           
        loc,scale = self.encoder_rna_zn(xs_rna)
        return loc,scale
    
    def _get_atac_basal_embedding(self, xs_atac):           
        loc,scale = self.encoder_atac_zn(xs_atac)
        return loc,scale
    
    def get_rna_basal_embedding(self, 
                             xs_rna, 
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
        xs_rna = self.preprocess(xs_rna,'rna')
        xs_rna = convert_to_tensor(xs_rna, device='cpu')
        dataset = CustomDataset(xs_rna)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                zns,_ = self._get_rna_basal_embedding(X_batch)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z
    
    def get_atac_basal_embedding(self, 
                             xs_atac, 
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
        xs_atac = self.preprocess(xs_atac,'atac')
        xs_atac = convert_to_tensor(xs_atac, device='cpu')
        dataset = CustomDataset(xs_atac)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                zns,_ = self._get_atac_basal_embedding(X_batch)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z
    
    def _rna_code(self, xs_rna):
        zns,_ = self._get_rna_basal_embedding(xs_rna)
        alpha = self.encoder_rna_n(zns)
        return alpha
    
    def rna_code(self, xs_rna, batch_size=1024, show_progress=True):
        xs_rna = self.preprocess(xs_rna,'rna')
        xs_rna = convert_to_tensor(xs_rna, device='cpu')
        dataset = CustomDataset(xs_rna)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        A = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                a = self._rna_code(X_batch)
                A.append(tensor_to_numpy(a))
                pbar.update(1)

        A = np.concatenate(A)
        return A
    
    def _atac_code(self, xs_atac):
        zns,_ = self._get_atac_basal_embedding(xs_atac)
        alpha = self.encoder_atac_n(zns)
        return alpha
    
    def atac_code(self, xs_atac, batch_size=1024, show_progress=True):
        xs_atac = self.preprocess(xs_atac,'atac')
        xs_atac = convert_to_tensor(xs_atac, device='cpu')
        dataset = CustomDataset(xs_atac)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        A = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                a = self._atac_code(X_batch)
                A.append(tensor_to_numpy(a))
                pbar.update(1)

        A = np.concatenate(A)
        return A
    
    def _rna_soft_assignments(self, xs_rna):
        alpha = self._rna_code(xs_rna)
        alpha = self.softmax(alpha)
        return alpha
    
    def rna_soft_assignments(self, xs_rna, batch_size=1024, show_progress=True):
        """
        Map cells to metacells and return the probabilistic values of metacell assignments
        """
        xs_rna = self.preprocess(xs_rna,'rna')
        xs_rna = convert_to_tensor(xs_rna, device='cpu')
        dataset = CustomDataset(xs_rna)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        A = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                a = self._rna_soft_assignments(X_batch)
                A.append(tensor_to_numpy(a))
                pbar.update(1)

        A = np.concatenate(A)
        return A
    
    def _atac_soft_assignments(self, xs_atac):
        alpha = self._atac_code(xs_atac)
        alpha = self.softmax(alpha)
        return alpha
    
    def atac_soft_assignments(self, xs_atac, batch_size=1024, show_progress=True):
        """
        Map cells to metacells and return the probabilistic values of metacell assignments
        """
        xs_atac = self.preprocess(xs_atac,'atac')
        xs_atac = convert_to_tensor(xs_atac, device='cpu')
        dataset = CustomDataset(xs_atac)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        A = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                a = self._atac_soft_assignments(X_batch)
                A.append(tensor_to_numpy(a))
                pbar.update(1)

        A = np.concatenate(A)
        return A
    
    def _rna_hard_assignments(self, xs_rna):
        alpha = self._rna_code(xs_rna)
        res, ind = torch.topk(alpha, 1)
        ns = torch.zeros_like(alpha).scatter_(1, ind, 1.0)
        return ns
    
    def rna_hard_assignments(self, xs_rna, batch_size=1024, show_progress=True):
        """
        Map cells to metacells and return the assigned metacell identities.
        """
        xs_rna = self.preprocess(xs_rna,'rna')
        xs_rna = convert_to_tensor(xs_rna, device='cpu')
        dataset = CustomDataset(xs_rna)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        A = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                a = self._rna_hard_assignments(X_batch)
                A.append(tensor_to_numpy(a))
                pbar.update(1)

        A = np.concatenate(A)
        return A
    
    def _atac_hard_assignments(self, xs_atac):
        alpha = self._rna_code(xs_atac)
        res, ind = torch.topk(alpha, 1)
        ns = torch.zeros_like(alpha).scatter_(1, ind, 1.0)
        return ns
    
    def atac_hard_assignments(self, xs_atac, batch_size=1024, show_progress=True):
        """
        Map cells to metacells and return the assigned metacell identities.
        """
        xs_atac = self.preprocess(xs_atac,'atac')
        xs_atac = convert_to_tensor(xs_atac, device='cpu')
        dataset = CustomDataset(xs_atac)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        A = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for X_batch, _ in dataloader:
                X_batch = X_batch.to(self.get_device())
                a = self._atac_hard_assignments(X_batch)
                A.append(tensor_to_numpy(a))
                pbar.update(1)

        A = np.concatenate(A)
        return A
    
    def rna_predict(self, xs_rna, perturb, library_sizes=None, show_progress=True):
        perturbs_reference = np.array(perturbs_reference)
        perturbs_predict = np.unique(perturbs_predict)
        
        # basal embedding
        zs = self.get_rna_basal_embedding(xs_rna)
        # shift
        dzs = self.get_rna_cell_shift(xs_rna, perturb_us=perturb, show_progress=show_progress)          
        
        zs = zs + dzs
        
        if library_sizes is None:
            library_sizes = np.sum(xs_rna, axis=1, keepdims=True)
        elif type(library_sizes) == list:
            library_sizes = np.array(library_sizes)
            library_sizes = library_sizes.reshape(-1,1)
        elif len(library_sizes.shape)==1:
            library_sizes = library_sizes.reshape(-1,1)
            
        counts = self.get_counts('rna', zs, library_sizes=library_sizes, show_progress=show_progress)
        log_mu = self.get_rna_log_mu(zs, show_progress=show_progress)
        
        return counts, log_mu
    
    def atac_predict(self, xs_atac, perturb, library_sizes=None, show_progress=True):
        perturbs_reference = np.array(perturbs_reference)
        perturbs_predict = np.unique(perturbs_predict)
        
        # basal embedding
        zs = self.get_atac_basal_embedding(xs_atac)
        # shift
        dzs = self.get_atac_cell_shift(xs_atac, perturb_us=perturb, show_progress=show_progress)          
        
        zs = zs + dzs
        
        if library_sizes is None:
            library_sizes = np.sum(xs_atac, axis=1, keepdims=True)
        elif type(library_sizes) == list:
            library_sizes = np.array(library_sizes)
            library_sizes = library_sizes.reshape(-1,1)
        elif len(library_sizes.shape)==1:
            library_sizes = library_sizes.reshape(-1,1)
            
        counts = self.get_counts('atac', zs, library_sizes=library_sizes, show_progress=show_progress)
        log_mu = self.get_atac_log_mu(zs, show_progress=show_progress)
        
        return counts, log_mu
    
    def _rna_cell_shift(self, rna_zs, perturb):
        ms = self.perturb_rna_effect([perturb, rna_zs])
        return ms 
    
    def _atac_cell_shift(self, atac_zs, perturb):
        ms = self.perturb_atac_effect([perturb, atac_zs])
        return ms 

    def get_rna_cell_shift(self, 
                             xs_rna, 
                             perturb_us,
                             use_codebook: bool = True,
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
        if use_codebook:
            zs = self.rna_codebook_map(xs_rna, soft_assign=soft_assign, show_progress=show_progress)
        else:
            zs = self.get_rna_basal_embedding(xs_rna, show_progress=show_progress)
        zs = convert_to_tensor(zs, device='cpu')
        ps = convert_to_tensor(perturb_us, device='cpu')
        dataset = CustomDataset(zs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for Z_batch, idx in dataloader:
                Z_batch = Z_batch.to(self.get_device())
                P_batch = ps[idx].to(self.get_device())
                zns = self._rna_cell_shift(Z_batch, P_batch)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z
    
    def get_atac_cell_shift(self, 
                             xs_atac, 
                             perturb_us,
                             use_codebook: bool = True,
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
        if use_codebook:
            zs = self.atac_codebook_map(xs_atac, soft_assign=soft_assign, show_progress=show_progress)
        else:
            zs = self.get_atac_basal_embedding(xs_atac, show_progress=show_progress)
        zs = convert_to_tensor(zs, device='cpu')
        ps = convert_to_tensor(perturb_us, device='cpu')
        dataset = CustomDataset(zs)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        Z = []
        with tqdm(total=len(dataloader), disable=not show_progress, desc='', unit='batch') as pbar:
            for Z_batch, idx in dataloader:
                Z_batch = Z_batch.to(self.get_device())
                P_batch = ps[idx].to(self.get_device())
                zns = self._atac_cell_shift(Z_batch, P_batch)
                Z.append(tensor_to_numpy(zns))
                pbar.update(1)

        Z = np.concatenate(Z)
        return Z
    
    def _rna_log_mu(self, zs):
        return self.decoder_rna_log_mu(zs)
    
    def _atac_log_mu(self, zs):
        return self.decoder_atac_log_mu(zs)
    
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
    
    def get_rna_log_mu(self, zs, batch_size: int = 1024, show_progress=True):
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
                r = self._rna_log_mu(Z_batch)
                R.append(tensor_to_numpy(r))
                pbar.update(1)

        R = np.concatenate(R)
        return R
    
    def get_atac_log_mu(self, zs, batch_size: int = 1024, show_progress=True):
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
                r = self._atac_log_mu(Z_batch)
                R.append(tensor_to_numpy(r))
                pbar.update(1)

        R = np.concatenate(R)
        return R
    
    def _count(self, modality, log_mu, library_size=None):
        if modality=='rna':
            loss_func = self.rna_loss_func
        if modality=='atac':
            loss_func = self.atac_loss_func
            
        if loss_func == 'bernoulli':
            counts = dist.Bernoulli(logits=log_mu).to_event(1).mean
        elif loss_func == 'negbinomial':
            counts = log_mu.exp()
        else:
            rate = log_mu.exp()
            theta = dist.DirichletMultinomial(total_count=1, concentration=rate).mean
            counts = theta * library_size
        return counts
    
    def get_counts(self, modality, zs, library_sizes, batch_size: int = 1024, show_progress=True):
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

        zs = convert_to_tensor(zs, device='cpu')
        
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
                if modality=='rna':
                    log_mu = self._rna_log_mu(Z_batch)
                else:
                    log_mu = self._atac_log_mu(Z_batch)
                counts = self._count(modality, log_mu, L_batch)
                E.append(tensor_to_numpy(counts))
                pbar.update(1)
        
        E = np.concatenate(E)
        return E
    
    def preprocess(self, xs, modality, threshold=0):
        if modality=='rna':
            loss_func = self.rna_loss_func
        if modality=='atac':
            loss_func = self.atac_loss_func
            
        if loss_func == 'bernoulli':
            ad = sc.AnnData(xs)
            binarize(ad, threshold=threshold)
            xs = ad.X.copy()
        elif loss_func in ['poisson','multinomial']:
            xs = np.round(xs)
            
        if sparse.issparse(xs):
            xs = xs.toarray()
        return xs 
    
    def fit(self, 
            xs_rna,
            xs_atac, 
            us = None, 
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
        Train the DensityFlowMO2 model.

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
            the Python script or Jupyter notebook. It is OK if it is used when runing DensityFlowMO2 in the shell command.
        show_progress: bool
            verbose on or off
        """
        xs_rna = self.preprocess(xs_rna, 'rna', threshold=threshold)
        xs_rna = convert_to_tensor(xs_rna, dtype=self.dtype, device='cpu')
        xs_atac = self.preprocess(xs_atac, 'atac', threshold=threshold)
        xs_atac = convert_to_tensor(xs_atac, dtype=self.dtype, device='cpu')
        if us is not None:
            us = convert_to_tensor(us, dtype=self.dtype, device='cpu')
        if cs is not None:
            cs = convert_to_tensor(cs, dtype=self.dtype, device='cpu')

        dataset = CustomDataset(xs_rna)
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
        
        rna_guide = config_enumerate(self.rna_guide, config_enum, expand=True)
        rna_loss = SVI(self.rna_model, rna_guide, scheduler, loss=elbo)

        atac_guide = config_enumerate(self.atac_guide, config_enum, expand=True)
        atac_loss = SVI(self.atac_model, atac_guide, scheduler, loss=elbo)
        
        cross_guide = config_enumerate(self.cross_guide, config_enum, expand=True)
        cross_loss = SVI(self.cross_model, cross_guide, scheduler, loss=elbo)
        
        # loss functions
        losses = [rna_loss,atac_loss,cross_loss]
        num_losses = len(losses)

        with tqdm(total=num_epochs, disable=not show_progress, desc='Training', unit='epoch') as pbar:
            for epoch in range(num_epochs):
                epoch_losses = [0.0] * num_losses
                for batch_x_rna, idx in dataloader:
                    batch_x_rna = batch_x_rna.to(self.get_device())
                    batch_x_atac = xs_atac[idx].to(self.get_device())
                    batch_u,batch_c = None,None
                    if us is not None:
                        batch_u = us[idx].to(self.get_device())
                    if cs is not None:
                        batch_c = cs[idx].to(self.get_device())

                    # single-omics
                    # RNA
                    loss_id = 0
                    new_loss = losses[loss_id].step(xs_rna=batch_x_rna, us=batch_u, cs=batch_c)
                    epoch_losses[loss_id] += new_loss
                    
                    # ATAC
                    loss_id = 1
                    new_loss = losses[loss_id].step(xs_atac=batch_x_atac, us=batch_u, cs=batch_c)
                    epoch_losses[loss_id] += new_loss
                    
                    # cross-omics
                    with torch.no_grad():
                        rna_ns_logits = self._rna_code(batch_x_rna).detach().clone()
                        atac_ns_logits = self._atac_code(batch_x_atac).detach().clone()
                        
                    # cross-omics
                    loss_id = 2
                    new_loss = losses[loss_id].step(rna_ns_logits=rna_ns_logits, atac_ns_logits=atac_ns_logits)
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
                
        print(f"🧬 DensityFlowMO2MO Initialized:")
        print(f"   - Codebook size: {model.code_size}")
        print(f"   - Latent Dimension: {model.latent_dim}")
        print(f"   - RNA Dimension: {model.rna_dim}")
        print(f"   - ATAC Dimension: {model.atac_dim}")
        print(f"   - Hidden Dimensions: {model.hidden_layers}")
        print(f"   - Device: {model.get_device()}")
        print(f"   - Parameters: {sum(p.numel() for p in model.parameters()):,}")
        
        return model
        
