# DensityFlow
 A deep additive model for learning perturbation semantics.

## Installation
1. Create a virtual environment
```bash
conda create -n densityflow python=3.10 scipy numpy pandas scikit-learn && conda activate densityflow
```

2. Install [PyTorch](https://pytorch.org/get-started/locally/) following the official instruction. 
```bash
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

3. Install DensityFlow
```bash
pip3 install DensityFlow
```

## Example
Dataset used in this example is obtained from [scPerturb](https://zenodo.org/records/13350497)

```
import re
import scanpy as sc


from DensityFlow import DensityFlow
from DensityFlow.perturb import LabelMatrix
from sklearn.model_selection import train_test_split
from eval_metrics import mmd_eval, r2_score_eval, pearson_eval


# perturbation information
pert_col = 'perturbation'
control_label = 'control'
loss_func = 'multinomial'

# load single cell data
adata = sc.read_h5ad('PapalexiSatija2021_eccite_RNA.h5ad')
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)

# normalize perturbation labels
adata.obs[pert_col] = [re.sub(r'g\d+$', '', s) for s in adata.obs[pert_col]]


# split single cell data into training and test subsets
cells_pert = adata[adata.obs[pert_col]!=control_label].obs_names
cells_train, cells_test = train_test_split(cells_pert, test_size= adata.shape[0] // 8)
cells_train = cells_train.tolist() + adata[adata.obs[pert_col]==control_label].obs_names.tolist()
adata_train = adata[cells_train].copy()
adata_test = adata[cells_test].copy()


# prepare data for training
xs = adata_train.X

lb = LabelMatrix()
us = lb.fit_transform(adata_train.obs[pert_col],control_label)
ln = lb.labels_

# training model
model = DensityFlow(input_size = xs.shape[1],
                    cell_factor_size=us.shape[1],
                    loss_func = loss_func,
                    seed=42,
                    use_cuda=True)

model.fit(xs, us=us, num_epochs=200, batch_size=1000, use_jax=True)


# save model
# DensityFlow.save_model(model, f'densityflow_{loss_func}_model.pt')

# load pre-trained model
# model = DensityFlow.load_model(f'densityflow_{loss_func}_model.pt')


# evaluation
def predict_pert_effect(ad,pert):
    ad = ad.copy()
    xs_pert = ad.X.toarray()
    zs_basal = model.get_basal_embedding(xs_pert, show_progress=False)

    ind = int(np.where(ln==pert)[0])
    us_pert = np.ones([xs_pert.shape[0],1])
    dzs = model.get_cell_shift(ad.X.toarray(), perturb_idx=ind, perturb_us=us_pert, show_progress=False)
    
    counts = model.get_counts(zs_basal+dzs, library_sizes=ad.X.sum(1), show_progress=False)
    return counts.copy()


results = []
pert_sets = adata_test.obs[pert_col].unique().tolist()
i = 0
for pert in pert_sets:
    i += 1
    print(f'{i}/{len(pert_sets)}')
    
    if pert==control_label:
        continue
    
    ad_test = adata_test[adata_test.obs[pert_col]==pert].copy()
    xs_test = ad_test.X.toarray()
    
    ind = np.random.choice(np.arange(adata_control.shape[0]), size=ad_test.shape[0], replace=True)
    ad_ctrl = adata_control[ind].copy()
    ad_ctrl.obs_names_make_unique()
    xs_basal = ad_ctrl.X.toarray()
    
    xs_test_pred = predict_pert_effect(ad_test, pert)
    
    xs_test_pred = xs_test_pred.astype(float)
    xs_test = xs_test.astype(float)
    xs_basal = xs_basal.astype(float)
    
    mmd_value=mmd_eval(xs_test_pred, xs_test)
    r2 = r2_score_eval(xs_test_pred, xs_test)
    pr = pearson_eval(xs_test_pred-xs_basal,xs_test-xs_basal)
    print(f'mmd:{mmd_value}; r2:{r2}; pearson:{pr}')
    results.append({'mmd':mmd_value,'r2':r2,'pearson':pr})


df = pd.DataFrame(results)
df.mean(0)
```


