import numpy as np
from scipy.interpolate import griddata
from scipy.spatial.distance import pdist, squareform
from sklearn.decomposition import PCA
from scipy.stats import pearsonr
from sklearn.neighbors import NearestNeighbors

class VectorFieldEval:
    def __init__(self):
        pass 
    
    def directional_alignment(self, vectors):
        return weighted_alignment(vectors=vectors)
        
    def flow_coherence(self, vectors):
        return pca_based_coherence(vectors=vectors)
        
    def momentum_flow_metric(self, vectors, masses=None):
        return momentum_flow_metric(vectors=vectors, masses=masses)
    
    def divergence(self, points, vectors, grid_resolution=30):
        # 提取坐标和向量分量
        x_coords = points[:, 0]
        y_coords = points[:, 1]
        u_components = vectors[:, 0]  # x方向分量
        v_components = vectors[:, 1]  # y方向分量
    
        # 创建规则网格
        x_grid = np.linspace(x_coords.min(), x_coords.max(), grid_resolution)
        y_grid = np.linspace(y_coords.min(), y_coords.max(), grid_resolution)
        X, Y = np.meshgrid(x_grid, y_grid)
    
        # 插值到网格
        U_grid = griddata((x_coords, y_coords), u_components, (X, Y), method='linear')
        V_grid = griddata((x_coords, y_coords), v_components, (X, Y), method='linear')
    
        # 计算散度
        dU_dx = np.gradient(U_grid, x_grid, axis=1)
        dV_dy = np.gradient(V_grid, y_grid, axis=0)
        divergence = dU_dx + dV_dy
        divergence[np.isnan(divergence)] = 0
        
        return divergence
    
    def movement_stats(self,vectors):
        return calculate_movement_stats(vectors)
    
    def direction_stats(self, vectors):
        return calculate_direction_stats(vectors)
    
    def movement_energy(self, vectors, masses=None):
        return calculate_movement_energy(vectors, masses)
    
    def movement_divergence(self, positions, vectors):
        return calculate_movement_divergence(positions, vectors)

        
def calculate_movement_stats(vectors):
    """
    计算移动矢量的基本统计量
    """
    # 计算每个矢量的模长（移动距离）
    distances = np.linalg.norm(vectors, axis=1)
    
    stats = {
        'total_movement': np.sum(distances),
        'mean_distance': np.mean(distances),
        'median_distance': np.median(distances),
        'std_distance': np.std(distances),
        'max_distance': np.max(distances),
        'min_distance': np.min(distances),
        'total_points': len(vectors)
    }
    
    return stats, distances

def calculate_direction_stats(vectors):
    """
    计算移动方向的一致性
    """
    # 单位向量
    unit_vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    
    # 平均方向向量
    mean_direction = np.mean(unit_vectors, axis=0)
    mean_direction_norm = np.linalg.norm(mean_direction)
    
    # 方向一致性（0-1，1表示完全一致）
    direction_consistency = mean_direction_norm
    
    return {
        'direction_consistency': direction_consistency,
        'mean_direction': mean_direction,
        'direction_variance': 1 - direction_consistency  # 方向分散度
    }

def calculate_movement_energy(vectors, masses=None):
    """
    计算移动的能量（假设每个点有质量）
    """
    if masses is None:
        masses = np.ones(len(vectors))  # 默认单位质量
    
    # 动能 = 0.5 * mass * velocity^2
    speeds_squared = np.sum(vectors**2, axis=1)
    kinetic_energy = 0.5 * masses * speeds_squared
    
    return {
        'total_energy': np.sum(kinetic_energy),
        'mean_energy': np.mean(kinetic_energy),
        'energy_std': np.std(kinetic_energy)
    }

def calculate_movement_divergence(positions, vectors):
    """
    计算移动的散度（衡量扩张/收缩）
    """
    
    # 计算移动前后的位置
    new_positions = positions + vectors
    
    # 计算位置变化的协方差
    orig_cov = np.cov(positions.T)
    new_cov = np.cov(new_positions.T)
    
    # 体积变化（行列式比值）
    volume_ratio = np.linalg.det(new_cov) / np.linalg.det(orig_cov)
    
    return {
        'volume_expansion': volume_ratio,  # >1扩张, <1收缩
        'expansion_factor': volume_ratio**(1/positions.shape[1])
    }
    

def directional_alignment(vectors):
    """
    计算向量场的方向一致性
    返回值: 0-1之间，1表示完全一致
    """
    # 归一化向量
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    unit_vectors = vectors / (norms + 1e-8)  # 避免除零
    
    # 计算平均方向向量
    mean_direction = np.mean(unit_vectors, axis=0)
    mean_direction_norm = np.linalg.norm(mean_direction)
    
    return mean_direction_norm

def weighted_alignment(vectors):
    """
    根据移动强度加权的方向一致性
    """
    norms = np.linalg.norm(vectors, axis=1)
    unit_vectors = vectors / norms[:, np.newaxis]
    
    # 用移动强度加权
    weights = norms / np.sum(norms)
    weighted_mean = np.sum(unit_vectors * weights[:, np.newaxis], axis=0)
    
    return np.linalg.norm(weighted_mean)


def flow_coherence_index(vectors, alpha=0.5):
    """
    流动一致性指数：综合方向和强度
    Args:
        alpha: 方向权重 (0-1)，强度权重为 1-alpha
    Returns:
        0-1之间的值，越大表示越一致的大规模移动
    """
    # 1. 方向一致性成分
    norms = np.linalg.norm(vectors, axis=1)
    unit_vectors = vectors / norms[:, np.newaxis]
    direction_consistency = np.linalg.norm(np.mean(unit_vectors, axis=0))
    
    # 2. 移动强度成分（标准化）
    intensity = np.mean(norms) / (np.std(norms) + 1e-8)  # 均值/标准差
    normalized_intensity = 1 - np.exp(-intensity)  # 映射到0-1
    
    # 3. 综合指标
    fci = alpha * direction_consistency + (1 - alpha) * normalized_intensity
    return fci, direction_consistency, normalized_intensity


def pca_based_coherence(vectors):
    """
    基于PCA的流动一致性分析
    """    
    # 计算协方差矩阵的特征值
    cov_matrix = np.cov(vectors.T)
    eigenvalues = np.linalg.eigvals(cov_matrix)
    eigenvalues = np.sort(eigenvalues)[::-1]  # 降序排列
    
    # 第一主成分解释的方差比例
    explained_variance_ratio = eigenvalues[0] / np.sum(eigenvalues)
    
    # 方向一致性（第一主成分的方向重要性）
    pca = PCA(n_components=1)
    pca.fit(vectors)
    principal_component = pca.components_[0]
    
    # 计算向量与主成分的夹角一致性
    unit_vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    cos_similarities = np.abs(np.dot(unit_vectors, principal_component))
    alignment_with_pc = np.mean(cos_similarities)
    
    return explained_variance_ratio, alignment_with_pc

def momentum_flow_metric(vectors, masses=None):
    """
    类比物理动量的一致性度量
    """
    if masses is None:
        masses = np.ones(len(vectors))  # 默认单位质量
    
    # 计算总动量
    momenta = vectors * masses[:, np.newaxis]  # p = m*v
    total_momentum = np.sum(momenta, axis=0)
    
    # 计算总动能
    kinetic_energies = 0.5 * masses * np.sum(vectors**2, axis=1)
    total_energy = np.sum(kinetic_energies)
    
    # 一致性指标：总动量大小 / 总能量（类比速度一致性）
    if total_energy > 0:
        coherence = np.linalg.norm(total_momentum) / (2 * total_energy) ** 0.5
    else:
        coherence = 0
    
    # 方向一致性（动量方向与个体方向的平均对齐）
    if np.linalg.norm(total_momentum) > 0:
        momentum_direction = total_momentum / np.linalg.norm(total_momentum)
        unit_vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        directional_alignment = np.mean(np.abs(np.dot(unit_vectors, momentum_direction)))
    else:
        directional_alignment = 0
    
    return coherence, directional_alignment, np.linalg.norm(total_momentum)



def multi_scale_coherence(vectors, positions=None, scale_factors=[1.0, 0.5, 0.1]):
    """
    多尺度一致性分析：检测不同空间尺度的一致性
    """
    if positions is None:
        positions = np.random.rand(len(vectors), 2)  # 随机位置
    
    coherence_scores = []
    
    for scale in scale_factors:
        # 根据空间距离加权
        if len(positions) > 0:
            distances = squareform(pdist(positions))
            weights = np.exp(-distances / scale)  # 距离衰减权重
            
            # 计算加权方向一致性
            unit_vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
            weighted_avg = np.zeros_like(unit_vectors[0])
            
            for i in range(len(vectors)):
                neighbor_weights = weights[i] / np.sum(weights[i])
                weighted_avg += np.sum(unit_vectors * neighbor_weights[:, np.newaxis], axis=0)
            
            scale_coherence = np.linalg.norm(weighted_avg) / len(vectors)
            coherence_scores.append(scale_coherence)
        else:
            coherence_scores.append(directional_alignment(vectors))
    
    return dict(zip(scale_factors, coherence_scores))

def vector_field_coherence_score(vectors, positions=None, weights=None):
    """
    向量场一致性综合评分 (0-100分)
    """
    # 1. 基础方向一致性 (0-1)
    dir_consistency = directional_alignment(vectors)
    
    # 2. 移动强度指标
    magnitudes = np.linalg.norm(vectors, axis=1)
    intensity_score = np.mean(magnitudes) / (np.std(magnitudes) + 1e-8)
    intensity_score = min(1.0, intensity_score / 3.0)  # 标准化到0-1
    
    # 3. 空间相关性（如果有位置信息）
    if positions is not None and len(positions) > 10:
        nbrs = NearestNeighbors(n_neighbors=5).fit(positions)
        distances, indices = nbrs.kneighbors(positions)
        
        neighbor_correlations = []
        for i, neighbors in enumerate(indices):
            if len(neighbors) > 1:
                # 计算与邻居的方向相似度
                unit_vec = vectors[i] / np.linalg.norm(vectors[i])
                neighbor_vecs = vectors[neighbors[1:]]  # 排除自身
                neighbor_units = neighbor_vecs / np.linalg.norm(neighbor_vecs, axis=1, keepdims=True)
                correlations = np.abs(np.dot(neighbor_units, unit_vec))
                neighbor_correlations.extend(correlations)
        
        spatial_consistency = np.mean(neighbor_correlations) if neighbor_correlations else 0.5
    else:
        spatial_consistency = 0.5  # 默认值
    
    # 4. 综合评分 (加权平均)
    weights = weights or [0.4, 0.3, 0.3]  # 方向、强度、空间权重
    composite_score = (weights[0] * dir_consistency + 
                      weights[1] * intensity_score + 
                      weights[2] * spatial_consistency)
    
    # 转换为0-100分
    vfcs = composite_score * 100
    
    return {
        'vfcs': vfcs,
        'direction_consistency': dir_consistency * 100,
        'intensity_score': intensity_score * 100,
        'spatial_consistency': spatial_consistency * 100,
        'components': {
            'direction': dir_consistency,
            'intensity': intensity_score, 
            'spatial': spatial_consistency
        }
    }

