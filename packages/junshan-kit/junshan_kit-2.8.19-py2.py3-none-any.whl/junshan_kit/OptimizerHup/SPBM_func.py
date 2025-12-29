import torch, time
import cvxpy as cp
import numpy as np
np.set_printoptions(precision=8, suppress=True)


def add_cutting(x_his, f_his, g_his, x_k, g_k, loss, cutting_number = 10):
    x_his.append(x_k)
    g_his.append(g_k)
    f_his.append(loss)

    if len(f_his) > cutting_number:
        x_his.pop(0)
        g_his.pop(0)
        f_his.pop(0)
    
    return x_his, f_his, g_his


def cut_selection(x_his, f_his, g_his, M):
    selected_x, selected_f, selected_g = [], [], []
    for j in range(len(f_his)-1):
        lhs = f_his[-1]
        rhs = f_his[j] +  torch.dot(g_his[j],(x_his[-1] - x_his[j])) + M * torch.norm(g_his[j] - g_his[-1],p=2) ** 2
        # print((lhs.item(),rhs.item()))
        if lhs >= rhs:
            selected_x.append(x_his[j])
            selected_g.append(g_his[j])
            selected_f.append(f_his[j])

    selected_x.append(x_his[-1])
    selected_g.append(g_his[-1])
    selected_f.append(f_his[-1])

    return selected_x, selected_f, selected_g

def get_var(selected_x, selected_f, selected_g, delta):
    Gk = torch.stack(selected_g, dim=0).T  # 0.00059s
    rk = delta * torch.norm(Gk[-1,:], p=2)
    ek_list = []
    for _ in range(len(selected_f)):
        ek_list.append(selected_f[_] - selected_g[_] @ selected_x[_])

    xk_tensor = torch.stack(selected_x, dim=0)
    ek = torch.stack(ek_list, dim=0)

    return Gk, rk, ek

# <sub_pf>
def subproblem_pf(Gk, ek, xk, delta, Paras):
    # tensor ---> numpy  (0.05s)
    Gk_np = Gk.cpu().numpy()
    ek_np = ek.cpu().numpy()
    xk_np = xk.cpu().numpy()

    # print(xk_np.dtype,xk_np.dtype)  

    n, m = Gk_np.shape

    # define variable
    lambda_var = cp.Variable(m, nonneg=True)
    v = cp.Variable(nonneg=True)

    # objective function
    objective = cp.Minimize(
    (delta / 2) * cp.quad_form(lambda_var, Gk_np.T @ Gk_np) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)

    # constraints
    constraints: list[cp.Constraint] = [cp.sum(lambda_var) + v == 1]

    # SOVER
    problem = cp.Problem(objective, constraints)
    problem.solve()

    # print("lambda* =", lambda_var.value)
    # print("v* =", v.value)
    # print("Optimal Value =", problem.value)
    # print(type(lambda_var.value))

    lambda_GPU= torch.from_numpy(lambda_var.value).float().to(Paras['device']) # 1e-3
    # a  = xk_np - delta * Gk_np @ lambda_var.value
    
    xk =  xk - delta * Gk @ lambda_GPU

    return xk

# <sub_pf>


def subproblem_tr(Gk, ek, xk, rk, Paras):
    
    # tensor ---> numpy  (0.05s)
    Gk_np = Gk.cpu().numpy()
    ek_np = ek.cpu().numpy()
    xk_np = xk.cpu().numpy()
    rk_np = rk.cpu().numpy()

    # print(xk_np.dtype,xk_np.dtype)  

    n, m = Gk_np.shape
    A = Gk.T @ Gk

    # mu = 1e-4
    # A = Gk.T @ Gk +  mu * torch.eye(Gk.shape[1], device=Gk.device)

    Lk = torch.linalg.cholesky(A).T # In order to accelerate
    Lk_np = Lk.cpu().numpy()

    # print(f"Lk = {torch.norm(Lk,p=2)},Gk = {torch.norm(Gk,p=2)}") # euqal
    # assert False

    # define variable
    lambda_var = cp.Variable(m, nonneg=True)
    v = cp.Variable(nonneg=True)
    # s_time = time.time()
    # objective function
    # objective = cp.Minimize(
    # rk_np * cp.norm(Gk_np @ lambda_var, 2) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)
    
    objective = cp.Minimize(
    rk_np * cp.norm(Lk_np @ lambda_var, 2) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)

    # objective = cp.Minimize(
    # rk_np * cp.norm(Gk_np @ lambda_var, 2) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)
    

    # constraints
    constraints: list[cp.Constraint] = [cp.sum(lambda_var) + v == 1]

    # SOVER
    problem = cp.Problem(objective, constraints)
    problem.solve()
    # problem.solve(solver=cp.SCS, eps=1e-5)
    # problem.solve(solver=cp.ECOS, abstol=1e-8, reltol=1e-8, feastol=1e-8)
    
    # e_time = time.time()
    # print(e_time - s_time)

    # print("lambda* =", lambda_var.value)
    # print("v* =", v.value)
    # print("Optimal Value =", problem.value)
    # print(type(lambda_var.value))

    lambda_GPU= torch.from_numpy(lambda_var.value).float().to(Paras['device']) # 1e-3
    # a  = xk_np - delta * Gk_np @ lambda_var.value
    
    # print(f"xk = {xk.shape}, rk = {rk.shape},GK = {Gk.shape}, Lk = {Lk.shape}, lambda_GPU = {lambda_GPU}")

    # print(f"{torch.norm(Gk @ lambda_GPU.reshape(-1,1),p=2)}")
    # print(f"{torch.norm(Lk @ lambda_GPU.reshape(-1,1),p=2)}")
    # assert False

    xk =  xk.reshape(-1,1) - (rk / torch.norm(Gk @ lambda_GPU.reshape(-1,1),p=2)) * Gk @ lambda_GPU.reshape(-1,1)
    
    # xk = xk.reshape(-1,1) - (rk / torch.norm(Lk @ lambda_GPU.reshape(-1,1), p=2)) * (Gk @ lambda_GPU.reshape(-1,1))


# <SPBM-TR_Sub>
def subproblem_tr_2(Gk, ek, xk, rk, Paras):
    
    # tensor ---> numpy  (0.05s)
    Gk_np = Gk.cpu().numpy()
    ek_np = ek.cpu().numpy()
    xk_np = xk.cpu().numpy()
    rk_np = rk.cpu().numpy()

    # print(xk_np.dtype,xk_np.dtype)  

    n, m = Gk_np.shape
    A = Gk.T @ Gk

    # print(f'A = {A}')
    Lk = torch.linalg.cholesky(A).T # In order to accelerate

    Lk_np = Lk.cpu().numpy()

    # print(f"Lk = {Lk}")

    # print(f"Lk = {torch.norm(Lk,p=2)},Gk = {torch.norm(Gk,p=2)}") # euqal
    # assert False

    # define variable
    lambda_var = cp.Variable(m, nonneg=True)
    nu = cp.Variable(nonneg=True)
    # s_time = time.time()
    # objective function
    # objective = cp.Minimize(
    # rk_np * cp.norm(Gk_np @ lambda_var, 2) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)
    
    objective = cp.Minimize(
    rk_np * cp.norm(Lk_np @ lambda_var, 2) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)

    # objective = cp.Minimize(
    # rk_np * cp.norm(Gk_np @ lambda_var, 2) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)
    

    # constraints
    constraints: list[cp.Constraint] = [cp.sum(lambda_var) + nu == 1]

    # SOVER
    problem = cp.Problem(objective, constraints)
    problem.solve()
    # problem.solve(solver=cp.SCS, eps=1e-5)
    # problem.solve(solver=cp.ECOS, abstol=1e-8, reltol=1e-8, feastol=1e-8)
    
    # e_time = time.time()
    # print(e_time - s_time)

    # print("lambda* =", lambda_var.value)
    # print("nu* =", nu.value)
    # print("Optimal Value =", problem.value)
    # print(type(lambda_var.value))

    lambda_GPU= torch.from_numpy(lambda_var.value).float().to(Paras['device']) # 1e-3
    # a  = xk_np - delta * Gk_np @ lambda_var.value
    
    # print(f"xk = {xk.shape}, rk = {rk.shape},GK = {Gk.shape}, Lk = {Lk.shape}, lambda_GPU = {lambda_GPU}")

    # print(f"{torch.norm(Gk @ lambda_GPU.reshape(-1,1),p=2)}")
    # print(f"{torch.norm(Lk @ lambda_GPU.reshape(-1,1),p=2)}")
    # assert False

    # case:
    # xk =  xk.reshape(-1,1) - (rk / torch.norm(Gk @ lambda_GPU.reshape(-1,1),p=2)) * Gk @ lambda_GPU.reshape(-1,1)
    
    # xk = xk.reshape(-1,1) - (rk / torch.norm(Lk @ lambda_GPU.reshape(-1,1), p=2)) * (Gk @ lambda_GPU.reshape(-1,1))

    # return xk.reshape(-1)
    eps = 1e-6  
    g_lambda = Gk @ lambda_GPU.reshape(-1, 1)
    norm_g_lambda = torch.norm(g_lambda, p=2)

    # print(nu.value)

    if norm_g_lambda < eps:  ## 0.01s
        if lambda_var.value is None:
            raise ValueError("lambda_var has not been solved yet")

        v_star = np.dot(lambda_var.value, ek_np)
        # print(f"v = {v_star}")
        
        m = Gk.shape[1]
        mu = cp.Variable(m, nonneg=True)
        
        # 
        term1 = 0.25 * cp.sum_squares(Lk_np @ mu)
        term2 = mu @ (ek_np - v_star * np.ones(m) + Gk_np.T @ xk_np)
        
        objective = cp.Minimize(term1 - term2)
        problem = cp.Problem(objective)
        problem.solve()

        mu_GPU = torch.from_numpy(mu.value).float().to(Paras['device'])
        # print(mu_GPU)
        # Clamp all elements in mu_GPU to be at least 1e-8 to avoid numerical instability (e.g., division by zero or log of zero)

        # mu_GPU = torch.clamp(mu_GPU, min=1e-8) 

        xk = xk.reshape(-1,1) - 0.5 * Gk @ mu_GPU.reshape(-1,1) 

        # print(f"xk = {torch.norm(xk)}, Gk*mu = {Gk @ mu_GPU.reshape(-1,1)}")
        return xk.reshape(-1)

    # Otherwise, update normally.
    xk = xk.reshape(-1, 1) - (rk / norm_g_lambda) * g_lambda

    return xk.reshape(-1)
# <SPBM-TR_Sub>

# <SPBM_TR_NoneSpecial>
def subproblem_tr_NoneSpecial(Gk, ek, xk, rk, Paras):
    # tensor ---> numpy  (0.05s)
    Gk_np = Gk.cpu().numpy()
    ek_np = ek.cpu().numpy()
    xk_np = xk.cpu().numpy()
    rk_np = rk.cpu().numpy()

    n, m = Gk_np.shape
    A = Gk.T @ Gk

    Lk = torch.linalg.cholesky(A).T # In order to accelerate
    Lk_np = Lk.cpu().numpy()

    # define variable (dual)
    lambda_var = cp.Variable(m, nonneg=True)
    nu = cp.Variable(nonneg=True)

    # define objective function
    objective = cp.Minimize(
    rk_np * cp.norm(Lk_np @ lambda_var, 2) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)

    # constraints
    constraints: list[cp.Constraint] = [cp.sum(lambda_var) + nu == 1]

    # SOVER
    problem = cp.Problem(objective, constraints)
    problem.solve()

    lambda_GPU= torch.from_numpy(lambda_var.value).float().to(Paras['device']) # 1e-3

    if lambda_var.value is None:
        raise ValueError("lambda_var has not been solved yet")
    # calculate optimal value of primal problem

    Gk_xk = Gk_np.T @ xk_np.reshape(-1,1)
    # print(Gk_xk)
    # print(ek_np + Gk_xk)
    # print(lambda_var.value)
    v_star_item1 = np.dot(lambda_var.value, (ek_np + Gk_xk))
    v_star_item2 = rk_np * np.linalg.norm(Gk_np@lambda_var.value)
    
    v_star = v_star_item1 - v_star_item2

    m = Gk.shape[1]
    mu = cp.Variable(m, nonneg=True)
    
    # 
    term1 = 0.25 * cp.sum_squares(Lk_np @ mu)
    term2 = mu @ (ek_np - v_star * np.ones(m) + Gk_np.T @ xk_np)
    
    objective = cp.Minimize(term1 - term2)
    problem = cp.Problem(objective)
    problem.solve()

    mu_GPU = torch.from_numpy(mu.value).float().to(Paras['device'])
    # print(mu_GPU)

    xk = xk.reshape(-1,1) - 0.5 * Gk @ mu_GPU.reshape(-1,1) 

    # print(f"xk = {torch.norm(xk)}, Gk*mu = {Gk @ mu_GPU.reshape(-1,1)}")
    return xk.reshape(-1)
# <SPBM_TR_NoneSpecial>



def subproblem_tr_3(Gk, ek, xk, rk, Paras):
    
    # tensor ---> numpy  (0.05s)
    Gk_np = Gk.cpu().numpy()
    ek_np = ek.cpu().numpy()
    xk_np = xk.cpu().numpy()
    rk_np = rk.cpu().numpy()

    n, m = Gk_np.shape
    A = Gk.T @ Gk

    # print(f'A = {A}')
    Lk = torch.linalg.cholesky(A).T # In order to accelerate

    Lk_np = Lk.cpu().numpy()

    # define variable
    lambda_var = cp.Variable(m, nonneg=True)
    nu = cp.Variable(nonneg=True)
    
    objective = cp.Minimize(
    rk_np * cp.norm(Lk_np @ lambda_var, 2) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)

    # constraints
    constraints: list[cp.Constraint] = [cp.sum(lambda_var) + nu == 1]

    # SOVER
    problem = cp.Problem(objective, constraints)
    problem.solve()

    lambda_GPU= torch.from_numpy(lambda_var.value).float().to(Paras['device']) # 1e-3
    # a  = xk_np - delta * Gk_np @ lambda_var.value
    
    if lambda_var.value is None:
        raise ValueError("lambda_var has not been solved yet")

    v_star = np.dot(lambda_var.value, ek_np)
    # print(f"v = {v_star}")
    
    m = Gk.shape[1]
    mu = cp.Variable(m, nonneg=True)
    
    # Construct the objective function
    term1 = 0.25 * cp.sum_squares(Lk_np @ mu)
    term2 = mu @ (ek_np - v_star * np.ones(m) + Gk_np.T @ xk_np)
    
    objective = cp.Minimize(term1 - term2)
    problem = cp.Problem(objective)
    problem.solve()
    mu_GPU = torch.from_numpy(mu.value).float().to(Paras['device'])

    xk = xk.reshape(-1,1) - 0.5 * Gk @ mu_GPU.reshape(-1,1) 

    return xk.reshape(-1)
        


def subproblem_tr_NoneLower(Gk, ek, xk, rk, Paras):
    # tensor ---> numpy  (0.05s)
    Gk_np = Gk.cpu().numpy()
    ek_np = ek.cpu().numpy()
    xk_np = xk.cpu().numpy()
    rk_np = rk.cpu().numpy()

    # print(xk_np.dtype,xk_np.dtype)  

    n, m = Gk_np.shape
    A = Gk.T @ Gk

    # print(f'A = {A}')
    Lk = torch.linalg.cholesky(A).T # In order to accelerate

    Lk_np = Lk.cpu().numpy()

    lambda_var = cp.Variable(m, nonneg=True)
    nu = cp.Variable(nonneg=True)

    objective = cp.Minimize(
    rk_np * cp.norm(Lk_np @ lambda_var, 2) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)

    # constraints
    constraints = [cp.sum(lambda_var) == 1]


    problem = cp.Problem(objective, constraints) # type: ignore
    problem.solve()
    # problem.solve(solver=cp.SCS, eps=1e-5)
    # problem.solve(solver=cp.ECOS, abstol=1e-8, reltol=1e-8, feastol=1e-8)
    
    # e_time = time.time()
    # print(e_time - s_time)

    # print("lambda* =", lambda_var.value)
    # print("nu* =", nu.value)
    # print("Optimal Value =", problem.value)
    # print(type(lambda_var.value))

    lambda_GPU= torch.from_numpy(lambda_var.value).float().to(Paras['device']) # 1e-3
    # a  = xk_np - delta * Gk_np @ lambda_var.value
    
    # print(f"xk = {xk.shape}, rk = {rk.shape},GK = {Gk.shape}, Lk = {Lk.shape}, lambda_GPU = {lambda_GPU}")

    # print(f"{torch.norm(Gk @ lambda_GPU.reshape(-1,1),p=2)}")
    # print(f"{torch.norm(Lk @ lambda_GPU.reshape(-1,1),p=2)}")
    # assert False

    # case:
    # xk =  xk.reshape(-1,1) - (rk / torch.norm(Gk @ lambda_GPU.reshape(-1,1),p=2)) * Gk @ lambda_GPU.reshape(-1,1)
    
    # xk = xk.reshape(-1,1) - (rk / torch.norm(Lk @ lambda_GPU.reshape(-1,1), p=2)) * (Gk @ lambda_GPU.reshape(-1,1))

    # return xk.reshape(-1)
    
    eps = 1e-6  
    g_lambda = Gk @ lambda_GPU.reshape(-1, 1)
    norm_g_lambda = torch.norm(g_lambda, p=2)

    # print(nu.value)

    if norm_g_lambda < eps:  ## 0.01s
        if lambda_var.value is None:
            raise ValueError("lambda_var has not been solved yet")

        v_star = np.dot(lambda_var.value, ek_np)
        # print(f"v = {v_star}")
        
        m = Gk.shape[1]
        mu = cp.Variable(m, nonneg=True)
        
        # Construct the objective function
        term1 = 0.25 * cp.sum_squares(Lk_np @ mu)
        term2 = mu @ (ek_np - v_star * np.ones(m) + Gk_np.T @ xk_np)
        
        objective = cp.Minimize(term1 - term2)
        problem = cp.Problem(objective)
        problem.solve()

        mu_GPU = torch.from_numpy(mu.value).float().to(Paras['device'])
        # print(mu_GPU)
        # Clamp all elements in mu_GPU to be at least 1e-8 to avoid numerical instability (e.g., division by zero or log of zero)

        # mu_GPU = torch.clamp(mu_GPU, min=1e-8) 

        xk = xk.reshape(-1,1) - 0.5 * Gk @ mu_GPU.reshape(-1,1) 

        # print(f"xk = {torch.norm(xk)}, Gk*mu = {Gk @ mu_GPU.reshape(-1,1)}")
        return xk.reshape(-1)

    # therwise, update normally.
    xk = xk.reshape(-1, 1) - (rk / norm_g_lambda) * g_lambda
    return xk.reshape(-1)
    

def subproblem_pf_NoneLower(Gk, ek, xk, delta, Paras):
    # tensor ---> numpy  (0.05s)
    Gk_np = Gk.cpu().numpy()
    ek_np = ek.cpu().numpy()
    xk_np = xk.cpu().numpy()

    # print(xk_np.dtype,xk_np.dtype)  

    n, m = Gk_np.shape

    # define variable
    lambda_var = cp.Variable(m, nonneg=True)
    # v = cp.Variable(nonneg=True)

    # objective function
    objective = cp.Minimize(
    (delta / 2) * cp.quad_form(lambda_var, Gk_np.T @ Gk_np) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)

    # constraints
    constraints = [cp.sum(lambda_var) == 1]

    # SOVER
    problem = cp.Problem(objective, constraints) # type: ignore
    problem.solve()

    # print("lambda* =", lambda_var.value)
    # print("v* =", v.value)
    # print("Optimal Value =", problem.value)
    # print(type(lambda_var.value))

    lambda_GPU= torch.from_numpy(lambda_var.value).float().to(Paras['device']) # 1e-3
    # a  = xk_np - delta * Gk_np @ lambda_var.value
    
    xk =  xk - delta * Gk @ lambda_GPU

    return xk

def bundle(Gk, ek, xk, delta, Paras):
    # tensor ---> numpy  (0.05s)
    Gk_np = Gk.cpu().numpy()
    ek_np = ek.cpu().numpy()
    xk_np = xk.cpu().numpy()

    # print(xk_np.dtype,xk_np.dtype)  

    n, m = Gk_np.shape

    # define variable
    lambda_var = cp.Variable(m, nonneg=True)
    # v = cp.Variable(nonneg=True)

    # objective function
    objective = cp.Minimize(
    (delta / 2) * cp.quad_form(lambda_var, Gk_np.T @ Gk_np) - (Gk_np.T @ xk_np + ek_np) @ lambda_var)

    # constraints
    constraints = [cp.sum(lambda_var) == 1]

    # SOVER
    problem = cp.Problem(objective, constraints) # type: ignore
    problem.solve()

    # print("lambda* =", lambda_var.value)
    # print("v* =", v.value)
    # print("Optimal Value =", problem.value)
    # print(type(lambda_var.value))

    lambda_GPU= torch.from_numpy(lambda_var.value).float().to(Paras['device']) # 1e-3
    # a  = xk_np - delta * Gk_np @ lambda_var.value
    
    xk =  xk - delta * Gk @ lambda_GPU

    return xk


def subproblem_tr_primal(Gk, ek, xk, rk, Paras):
    
    # tensor ---> numpy  (0.05s)
    Gk_np = Gk.cpu().numpy()
    ek_np = ek.cpu().numpy()
    xk_np = xk.cpu().numpy()
    rk_np = rk.cpu().numpy()

    # print(Gk_np.shape)
    n, m = Gk_np.shape


    m_ones = np.ones(m)
    x = cp.Variable(n)
    v = cp.Variable()

    objective = cp.Minimize(v)

    constraints = [
        Gk_np.T @ x + ek_np <= v * m_ones,
        cp.norm(x - xk_np) <= rk_np,
        v >= 0
    ]

    problem = cp.Problem(objective, constraints) # type: ignore
    problem.solve()

    return torch.from_numpy(x.value).float().to(Paras['device'])


 








