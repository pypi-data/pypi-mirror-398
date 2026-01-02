# 该.py为zelas在机器学习领域的收官之作，此后无特殊情况将不再更新机器学习相关函数
import zelas2.shield as zs
import zelas2.shield_plus as zsp
import numpy as np
import multiprocessing as mp
from multiprocessing import shared_memory
from scipy.spatial import cKDTree
import zelas2.RedundancyElimination as zr

def _sigmoid(x):
    x = np.clip(x, -60, 60)
    return 1.0 / (1.0 + np.exp(-x))

def _rmse(y, yhat):
    e = y - yhat
    return np.sqrt(np.mean(e*e) + 1e-12)

def get_LAWI_mp_from_theta_rho(c_idx, theta_deg, rho, k=12, cpu=mp.cpu_count(), min_pts=8, normalize=True):
    """
    并行按截面计算 LAWI（输入已给 theta_deg 与 rho）
    - c_idx:     (M,) 截面编号（xyzic[:,4]）
    - theta_deg: (M,) 角度
    - rho:       (M,) 径向残差/凸起量

    返回:
    - lawi_all: (M,)
    """
    c_idx = np.asarray(c_idx)
    theta_deg = np.asarray(theta_deg)
    rho = np.asarray(rho)

    c_un = np.unique(c_idx)
    pool = mp.Pool(processes=cpu)

    # 为了回填不出错，这里每个任务只返回该截面的 lawi_cs（顺序与 mask 相同）
    tasks = []
    masks = []
    for c in c_un:
        mask = (c_idx == c)
        masks.append(mask)
        # tasks.append((theta_deg[mask], rho[mask], k, None, min_pts))
        tasks.append((theta_deg[mask], rho[mask], k, None))
    try:
        res_list = pool.starmap(get_LAWI_cs, tasks)
    finally:
        pool.close()
        pool.join()

    lawi_all = np.zeros(len(c_idx), dtype=float)
    for mask, lawi_cs in zip(masks, res_list):
        lawi_all[mask] = lawi_cs

    if normalize:
        p95 = np.percentile(lawi_all, 95)
        if p95 > 0:
            lawi_all = np.clip(lawi_all / p95, 0.0, 1.0)

    return np.nan_to_num(lawi_all, nan=0.0)

def get_LAWI_cs(theta_deg, rho, k=12, tau=None):
    """
    改进点：
    - 尖点显著性：P = min(ri-mL, ri-mR) (两侧都要回落)
    - 台阶抑制：level_gate = 1/(1+|mL-mR|/(|P|+eps))
    - 保留：线-弧不对称、斜率异号软门控
    """
    N = len(theta_deg)
    order = np.argsort(theta_deg)
    th = theta_deg[order]
    rr = rho[order]

    lai = np.zeros(N, dtype=float)

    if N < (2 * k + 1):
        out = np.zeros(N, dtype=float)
        out[order] = lai
        return out

    # tau 自适应
    if tau is None:
        dr = np.abs(np.diff(np.r_[rr, rr[0]]))
        med = np.median(dr)
        mad = np.median(np.abs(dr - med))
        tau = med + 1.4826 * mad + 1e-6

    eps = 1e-6

    for i in range(N):
        L = (i - np.arange(1, k + 1)) % N
        R = (i + np.arange(1, k + 1)) % N

        th0 = th[i]
        dth_L = th[L] - th0
        dth_R = th[R] - th0
        dth_L = (dth_L + 180) % 360 - 180
        dth_R = (dth_R + 180) % 360 - 180

        rL, rR = rr[L], rr[R]
        if np.ptp(dth_L) < 1e-6 or np.ptp(dth_R) < 1e-6:
            continue

        # --- left fits ---
        try:
            p1L = np.polyfit(dth_L, rL, 1)
            rmse1L = _rmse(rL, np.polyval(p1L, dth_L))
            p2L = np.polyfit(dth_L, rL, 2)
            rmse2L = _rmse(rL, np.polyval(p2L, dth_L))
        except Exception:
            continue
        GL = max(0.0, rmse1L - rmse2L)
        slopeL = float(p1L[0])

        # --- right fits ---
        try:
            p1R = np.polyfit(dth_R, rR, 1)
            rmse1R = _rmse(rR, np.polyval(p1R, dth_R))
            p2R = np.polyfit(dth_R, rR, 2)
            rmse2R = _rmse(rR, np.polyval(p2R, dth_R))
        except Exception:
            continue
        GR = max(0.0, rmse1R - rmse2R)
        slopeR = float(p1R[0])

        # line-like / arc-like
        SlineL = 1.0 / (1.0 + rmse1L) * 1.0 / (1.0 + GL)
        SarcL  = 1.0 / (1.0 + rmse2L) * _sigmoid(GL / tau)
        SlineR = 1.0 / (1.0 + rmse1R) * 1.0 / (1.0 + GR)
        SarcR  = 1.0 / (1.0 + rmse2R) * _sigmoid(GR / tau)

        # ---------- 关键改动：双侧尖点 + 台阶抑制 ----------
        mL = np.median(rL)
        mR = np.median(rR)

        # 两侧都要比尖点低：台阶边界会被压下去
        P = min(rr[i] - mL, rr[i] - mR)
        if P <= 0:
            continue

        # 台阶不对称抑制：左右平台差越大，越像设施边缘
        asym_level = abs(mL - mR) / (abs(P) + eps)
        level_gate = 1.0 / (1.0 + asym_level)

        # 斜率异号软门控（类“入”）
        sign_gate = _sigmoid((-slopeL * slopeR) / (abs(slopeL * slopeR) + eps))

        asym_shape = max(SlineL * SarcR, SarcL * SlineR)

        lai[i] = P * level_gate * sign_gate * asym_shape

    out = np.zeros(N, dtype=float)
    out[order] = lai
    return out

def _Ty_block(py, lawi, r_py, td_lawi, start, end):
    """
    在 (p,y) 平面里，对每个点看半径 r_py 邻域内：
    是否在 y 前后两侧都存在足够的高 LAWI 邻居
    """
    tree = cKDTree(py)
    Ty = np.zeros(end - start, dtype=float)
    eps = 1e-6

    for j, i in enumerate(range(start, end)):
        idx = tree.query_ball_point(py[i], r=r_py)
        if len(idx) <= 1:
            continue
        idx = np.array(idx, dtype=int)
        idx = idx[idx != i]

        # 只看高 LAWI 邻居
        good = lawi[idx] >= td_lawi
        if not np.any(good):
            continue
        idxg = idx[good]

        dy = py[idxg, 1] - py[i, 1]
        n_f = np.sum(dy > 0)   # 前方
        n_b = np.sum(dy < 0)   # 后方

        Ty[j] = min(n_f, n_b) / (max(n_f, n_b) + eps)

    return Ty

def get_Ty_mp(perimeter, y, lawi, r_py, td_lawi=None, cpu=mp.cpu_count()):
    """
    返回每点 Ty 连续性（0~1）
    - td_lawi: 判定“高 LAWI 邻居”的阈值，None -> 用分位数自适应
    """
    py = np.c_[perimeter, y]
    n = len(py)

    if td_lawi is None:
        # 自适应：只把上 15% 当“高 LAWI”
        td_lawi = float(np.percentile(lawi, 85))

    tik = zs.cut_down(n, cpu)  # 你工程里已有
    pool = mp.Pool(processes=cpu)
    try:
        res = [pool.apply_async(_Ty_block, args=(py, lawi, r_py, td_lawi, tik[i], tik[i+1]))
               for i in range(cpu)]
        Ty_all = np.zeros(n, dtype=float)
        for i, r in enumerate(res):
            Ty_all[tik[i]:tik[i+1]] = r.get()
    finally:
        pool.close()
        pool.join()

    return np.nan_to_num(Ty_all, nan=0.0)

def get_LAWI_mp(xyzic, cpu=mp.cpu_count(), k=12, min_pts=8, normalize=True,
                use_Ty=True, gamma=1.5, r_py=None):
    """
    返回最终 LAWI（含设施边缘抑制 + bolt hole 连续性抑制）

    - use_Ty: 是否启用沿Y连续性门控
    - gamma : Ty 的指数（1~2 常用）
    - r_py  : (p,y) 邻域半径；None 时自适应
    """
    ig = 10
    c_max = np.max(xyzic[:,4]) - ig
    c_min = np.min(xyzic[:,4]) + ig
    xyzic_min = xyzic[(xyzic[:,4] >= c_min) & (xyzic[:,4] <= c_max), :]

    xzrc = zs.fit_circle(xyzic_min[:, 0], xyzic_min[:, 2], xyzic_min[:, 4], num_cpu=cpu)
    x0 = float(np.mean(xzrc[:, 0]))
    z0 = float(np.mean(xzrc[:, 1]))
    R  = float(np.mean(xzrc[:, 2]))

    theta_deg = zs.get_angle_all(xyzic[:, [0, 2]], x0, z0, cpu_count=cpu)
    rho = np.sqrt((xyzic[:, 0] - x0) ** 2 + (xyzic[:, 2] - z0) ** 2) - R

    # 先算“改进后的 LAWI（截面并行）”
    lawi_all = get_LAWI_mp_from_theta_rho(
        c_idx=xyzic[:, 4],
        theta_deg=theta_deg,
        rho=rho,
        k=k,
        cpu=cpu,
        min_pts=min_pts,
        normalize=False   # 先别归一化，后面还要乘 Ty
    )

    # 计算 perimeter（p-y 平面用）
    perimeter = (theta_deg / 360.0) * (2.0 * np.pi * R)

    # --- bolt hole 抑制：沿Y连续性门控 ---
    if use_Ty:
        # 自适应 r_py：用点云在 y 方向的局部间距来估一下尺度
        # 经验：取 y 的 90分位邻近间距的 3~5 倍
        if r_py is None:
            # 粗略估计：按 y 排序后相邻差
            y_sorted = np.sort(xyzic[:, 1])
            dy = np.diff(y_sorted)
            dy = dy[dy > 1e-6]
            if len(dy) > 0:
                dy0 = float(np.percentile(dy, 90))
                r_py = max(3.0 * dy0, 0.02)  # 给个下限，避免过小
            else:
                r_py = 0.05

        Ty = get_Ty_mp(perimeter, xyzic[:, 1], lawi_all, r_py=r_py, td_lawi=None, cpu=cpu)
        lawi_all = lawi_all * (Ty ** gamma)

    # 最后再归一化到 0~1（可选）
    if normalize:
        p95 = np.percentile(lawi_all, 95)
        if p95 > 0:
            lawi_all = np.clip(lawi_all / p95, 0.0, 1.0)

    return np.nan_to_num(lawi_all, nan=0.0)