import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import scanpy as sc
from matplotlib.colors import ListedColormap


def plot_quiver(z_points, delta_z, method='pca', figsize=(6,4), dpi=200, 
                subsample=None, color_by=None, colormap='viridis', 
                point_size = 3, point_alpha=0.5,
                arrow_scale=1.0, arrow_width=0.002, alpha=0.8, no_title=False):
    """
    优化后的quiver可视化函数
    
    Args:
        z_points: 原始潜在空间点 [n_samples, n_dims]
        delta_z: 移动向量 [n_samples, n_dims]
        method: 降维方法 ('pca', 'variance', 'manual', 'umap')
        figsize: 图像大小
        dpi: 分辨率
        subsample: 随机采样的数据点数量 (None表示不采样)
        color_by: 颜色标签数组 [n_samples]
        colormap: 颜色映射名称或ListedColormap对象
        arrow_scale: 箭头缩放因子
        arrow_width: 箭头宽度
        alpha: 透明度
    """
    # 保存原始数据用于散点图
    original_z_points = z_points.copy()
    original_delta_z = delta_z.copy()
    original_color_by = color_by.copy() if color_by is not None else None
    
    # 数据采样（仅用于quiver）
    quiver_indices = None
    if subsample is not None and len(z_points) > subsample:
        quiver_indices = np.random.choice(len(z_points), subsample, replace=False)
        z_points_quiver = z_points[quiver_indices]
        delta_z_quiver = delta_z[quiver_indices]
        if color_by is not None:
            color_by_quiver = color_by[quiver_indices]
        else:
            color_by_quiver = None
        color_by_quiver=None
    else:
        z_points_quiver = z_points
        delta_z_quiver = delta_z
        color_by_quiver = color_by
        color_by_quiver=None
    
    # 降维投影（使用所有数据）
    if method == 'variance':
        variances = np.var(original_z_points, axis=0)
        dims = np.argsort(variances)[-2:]
        z_2d_all = original_z_points[:, dims]
        z_2d_quiver = z_points_quiver[:, dims]
        delta_z_2d = delta_z_quiver[:, dims]
        dim_names = [f'z[{d}]' for d in dims]
        
    elif method == 'pca':
        pca = PCA(n_components=2)
        z_2d_all = pca.fit_transform(original_z_points)
        z_2d_quiver = pca.transform(z_points_quiver)
        delta_z_2d = pca.transform(z_points_quiver + delta_z_quiver) - z_2d_quiver
        dim_names = ['PC1', 'PC2']
        
    elif method == 'manual':
        dims = [0, 1]
        z_2d_all = original_z_points[:, dims]
        z_2d_quiver = z_points_quiver[:, dims]
        delta_z_2d = delta_z_quiver[:, dims]
        dim_names = [f'z[{d}]' for d in dims]
        
    elif method == 'umap':
        # 使用所有数据进行UMAP降维
        ad = sc.AnnData(np.vstack([original_z_points, original_z_points+original_delta_z]))
        sc.pp.neighbors(ad)
        sc.tl.umap(ad)
        z_2d_all = ad[:len(original_z_points)].obsm['X_umap']
        z_2d_quiver = z_2d_all[quiver_indices] if quiver_indices is not None else z_2d_all
        delta_z_2d = ad[len(original_z_points):].obsm['X_umap'][quiver_indices] - z_2d_quiver if quiver_indices is not None else ad[len(original_z_points):].obsm['X_umap'] - z_2d_all
        dim_names = ['UMAP1', 'UMAP2']
    
    # 颜色处理（散点图使用所有数据，quiver使用采样数据）
    if original_color_by is not None:
        if isinstance(colormap, str):
            cmap = plt.get_cmap(colormap)
        else:
            cmap = colormap
        
        if original_color_by.dtype.kind in ['i', 'f']:  # 数值型标签
            # 所有数据的颜色
            colors_all = cmap(original_color_by / max(original_color_by.max(), 1e-8))
            # quiver数据的颜色
            if color_by_quiver is not None:
                colors_quiver = cmap(color_by_quiver / max(color_by_quiver.max(), 1e-8))
            else:
                colors_quiver = 'blue'
            cbar_label = 'Numeric Label'
        else:  # 类别型标签
            unique_labels = np.unique(original_color_by)
            if type(cmap)==dict:
                color_map = colormap
            else:
                color_map = {label: cmap(i/len(unique_labels)) 
                            for i, label in enumerate(unique_labels)}
            colors_all = [color_map[label] for label in original_color_by]
            if color_by_quiver is not None:
                colors_quiver = [color_map[label] for label in color_by_quiver]
            else:
                colors_quiver = 'blue'
            cbar_label = 'Class Label'
    else:
        colors_all = 'gray'
        colors_quiver = 'blue'
    
    # 绘制
    plt.figure(figsize=figsize, dpi=dpi)
    
    # 1. 首先绘制所有数据点的散点图
    if (original_color_by is not None) and (unique_labels is not None):
        for label in unique_labels:
            ind = color_by == label
            colors_label = [colors_all[ii] for ii in np.arange(z_2d_all.shape[0]) if ind[ii]]
            plt.scatter(z_2d_all[ind, 0], z_2d_all[ind, 1], 
                   c=colors_label, alpha=point_alpha, s=point_size, label=label)
            
        plt.legend(
        ncol = max(1, len(unique_labels) // 8),
        bbox_to_anchor=(1.00, 0.5),  # 图外右侧中间
        loc='center left',            # 锚点在左侧中间
        borderaxespad=0.0,            # 与图的间距
        frameon=False,                 # 显示边框
        fancybox=False,                # 圆角
        shadow=False,                  # 阴影
        #handletextpad=0.5,           # 点与文本间距
        markerscale=min(2*point_size,4)           # 关键：调整图例中点的大小（2倍）
        )
    else:
        plt.scatter(z_2d_all[:, 0], z_2d_all[:, 1], 
                   c=colors_all, alpha=point_alpha, s=point_size)
    
    # 2. 绘制quiver（仅采样数据）
    if color_by_quiver is not None and isinstance(color_by_quiver[0], str):
        for label in np.unique(color_by_quiver):
            mask = color_by_quiver == label
            plt.quiver(z_2d_quiver[mask, 0], z_2d_quiver[mask, 1],
                      delta_z_2d[mask, 0], delta_z_2d[mask, 1],
                      angles='xy', scale_units='xy', scale=1.0/arrow_scale,
                      color=colors_quiver[mask], width=arrow_width, alpha=alpha)
    else:
        q = plt.quiver(z_2d_quiver[:, 0], z_2d_quiver[:, 1],
                      delta_z_2d[:, 0], delta_z_2d[:, 1],
                      angles='xy', scale_units='xy', scale=1.0/arrow_scale,
                      color=colors_quiver, width=arrow_width, alpha=alpha)
        
        # 添加颜色条（数值型标签）
        if original_color_by is not None and original_color_by.dtype.kind in ['i', 'f']:
            plt.colorbar(plt.cm.ScalarMappable(
                norm=plt.Normalize(original_color_by.min(), original_color_by.max()),
                cmap=cmap), label=cbar_label)
    
    # 美化图形
    plt.xlabel(dim_names[0])
    plt.ylabel(dim_names[1])
    if not no_title:
        plt.title(f"Latent Space Movement ({method} projection)\n{len(z_points_quiver)}/{len(original_z_points)} points with vectors")
    else:
        plt.title('')
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.show()
    
    return z_2d_all, z_2d_quiver, delta_z_2d

def plot_quiver_old(z_points, delta_z, method='pca', figsize=(6,4), dpi=200):
    """
    从高维潜在空间选择2个维度进行quiver可视化
    """
    if method == 'variance':
        # 方法1: 选择方差最大的2个维度
        variances = np.var(z_points, axis=0)
        dims = np.argsort(variances)[-2:]  # 选择方差最大的两个维度
        dim_names = [f'z[{d}]' for d in dims]
        
    elif method == 'pca':
        # 方法2: 使用PCA的前两个主成分
        pca = PCA(n_components=2)
        z_2d = pca.fit_transform(z_points)
        delta_z_2d = pca.transform(z_points + delta_z) - z_2d
        dim_names = ['PC1', 'PC2']
        
    elif method == 'manual':
        # 方法3: 手动选择感兴趣的维度
        dims = [0, 1]  # 选择前两个维度
        z_2d = z_points[:, dims]
        delta_z_2d = delta_z[:, dims]
        dim_names = [f'z[{d}]' for d in dims]
        
    elif method == 'umap':
        ad = sc.AnnData(np.vstack([z_points, z_points+delta_z]))
        sc.pp.neighbors(ad)
        sc.tl.umap(ad)
        z_2d = ad[:z_points.shape[0]].obsm['X_umap']
        delta_z_2d = ad[z_points.shape[0]:].obsm['X_umap'] - z_2d
        dim_names = ['UMAP1', 'UMAP2']
    
    # 绘制quiver图
    plt.figure(figsize=figsize, dpi=dpi)
    plt.quiver(z_2d[:, 0], z_2d[:, 1], 
               delta_z_2d[:, 0], delta_z_2d[:, 1],
               angles='xy', scale_units='xy', scale=1,
               color='blue', alpha=0.6, width=0.005)
    
    plt.scatter(z_2d[:, 0], z_2d[:, 1], c='gray', alpha=0.5, s=10)
    plt.xlabel(dim_names[0])
    plt.ylabel(dim_names[1])
    plt.title(f"Latent Space Movement ({method} projection)")
    plt.grid(alpha=0.3)
    plt.show()
    
    return z_2d, delta_z_2d