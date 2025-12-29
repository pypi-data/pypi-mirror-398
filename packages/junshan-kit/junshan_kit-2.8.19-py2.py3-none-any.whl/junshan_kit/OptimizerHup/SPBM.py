from junshan_kit.OptimizerHup import SPBM_func
import torch, time, os
from torch.optim.optimizer import Optimizer
from torch.nn.utils import parameters_to_vector, vector_to_parameters


class PF(Optimizer):
    def __init__(self, params, model, hyperparams, Paras):
        defaults = dict()
        super().__init__(params, defaults)
        self.model = model
        self.cutting_num = hyperparams['cutting_number']
        self.M = hyperparams['M']
        self.delta = hyperparams['delta']
        self.Paras = Paras

        self.x_his, self.g_his, self.f_his = [], [], []

    def step(self, closure=None):
        if closure is None:
            raise RuntimeError("Closure required for CuttingPlaneOptimizer")
        
        # 清零梯度并前向计算
        loss = closure()
        
        with torch.no_grad():
            xk = parameters_to_vector(self.model.parameters())
            # print(torch.norm(xk))
            g_k = parameters_to_vector([p.grad if p.grad is not None else torch.zeros_like(p) for p in self.model.parameters()])

            # Add cutting plane
            x_his, f_his, g_his = SPBM_func.add_cutting(self.x_his, self.f_his, self.g_his,xk.detach().clone(), g_k.detach().clone(), loss.detach().clone(), self.cutting_num)

            ## Cut selection
            selected_x, selected_f, selected_g = SPBM_func.cut_selection(x_his, f_his, g_his, self.M)
                    
            # the coefficient of dual problem
            Gk, rk, ek = SPBM_func.get_var(selected_x, selected_f, selected_g, self.delta)
            
            # SOVER (dual)
            xk = SPBM_func.subproblem_pf(Gk, ek, xk, self.delta, self.Paras)
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())


        # 暂时返回 loss（tensor 类型）
        return loss
    
# <SPBM-TR>
class TR(Optimizer):
    def __init__(self, params, model, hyperparams, Paras):
        defaults = dict()
        super().__init__(params, defaults)
        self.model = model
        self.cutting_num = hyperparams['cutting_number']
        self.M = hyperparams['M']
        self.delta = hyperparams['delta']
        self.Paras = Paras

        self.x_his, self.g_his, self.f_his = [], [], []

    def step(self, closure=None):
        if closure is None:
            raise RuntimeError("Closure required for CuttingPlaneOptimizer")
        
        # Reset the gradient and perform forward computation
        loss = closure()
        
        with torch.no_grad():
            xk = parameters_to_vector(self.model.parameters())
            # print(torch.norm(xk))
            g_k = parameters_to_vector([p.grad if p.grad is not None else torch.zeros_like(p) for p in self.model.parameters()])

            # Add cutting plane
            x_his, f_his, g_his = SPBM_func.add_cutting(self.x_his, self.f_his, self.g_his,xk.detach().clone(), g_k.detach().clone(), loss.detach().clone(), self.cutting_num)

            ## Cut selection
            selected_x, selected_f, selected_g = SPBM_func.cut_selection(x_his, f_his, g_his, self.M)
                    
            # the coefficient of dual problem
            Gk, rk, ek = SPBM_func.get_var(selected_x, selected_f, selected_g, self.delta)
            
            # SOVER (dual)
            xk = SPBM_func.subproblem_tr_2(Gk, ek, xk, rk, self.Paras)
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())

        # tensor type
        return loss
# <SPBM-TR>  

# <SPBM-TR_NoneSpecial> 
class TR_NoneSpecial(Optimizer):
    def __init__(self, params, model, hyperparams, Paras):
        defaults = dict()
        super().__init__(params, defaults)
        self.model = model
        self.cutting_num = hyperparams['cutting_number']
        self.M = hyperparams['M']
        self.delta = hyperparams['delta']
        self.Paras = Paras

        self.x_his, self.g_his, self.f_his = [], [], []

    def step(self, closure=None):
        if closure is None:
            raise RuntimeError("Closure required for CuttingPlaneOptimizer")
        
        # Reset the gradient and perform forward computation
        loss = closure()
        
        with torch.no_grad():
            xk = parameters_to_vector(self.model.parameters())
            # print(torch.norm(xk))
            g_k = parameters_to_vector([p.grad if p.grad is not None else torch.zeros_like(p) for p in self.model.parameters()])

            # Add cutting plane
            x_his, f_his, g_his = SPBM_func.add_cutting(self.x_his, self.f_his, self.g_his,xk.detach().clone(), g_k.detach().clone(), loss.detach().clone(), self.cutting_num)

            ## Cut selection
            selected_x, selected_f, selected_g = SPBM_func.cut_selection(x_his, f_his, g_his, self.M)
                    
            # the coefficient of dual problem
            Gk, rk, ek = SPBM_func.get_var(selected_x, selected_f, selected_g, self.delta)
            
            # SOVER (dual)
            xk = SPBM_func.subproblem_tr_NoneSpecial(Gk, ek, xk, rk, self.Paras)
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())

        # tensor type
        return loss
# <SPBM-TR_NoneSpecial>  

class TR_primal(Optimizer):
    def __init__(self, params, model, hyperparams, Paras):
        defaults = dict()
        super().__init__(params, defaults)
        self.model = model
        self.cutting_num = hyperparams['cutting_number']
        self.M = hyperparams['M']
        self.delta = hyperparams['delta']
        self.Paras = Paras

        self.x_his, self.g_his, self.f_his = [], [], []

    def step(self, closure=None):
        if closure is None:
            raise RuntimeError("Closure required for CuttingPlaneOptimizer")
        
        # Reset the gradient and perform forward computation
        loss = closure()
        
        with torch.no_grad():
            xk = parameters_to_vector(self.model.parameters())
            # print(torch.norm(xk))
            g_k = parameters_to_vector([p.grad if p.grad is not None else torch.zeros_like(p) for p in self.model.parameters()])

            # Add cutting plane
            x_his, f_his, g_his = SPBM_func.add_cutting(self.x_his, self.f_his, self.g_his,xk.detach().clone(), g_k.detach().clone(), loss.detach().clone(), self.cutting_num)

            ## Cut selection
            selected_x, selected_f, selected_g = SPBM_func.cut_selection(x_his, f_his, g_his, self.M)
                    
            # the coefficient of dual problem
            Gk, rk, ek = SPBM_func.get_var(selected_x, selected_f, selected_g, self.delta)
            
            # SOVER (dual)
            xk = SPBM_func.subproblem_tr_primal(Gk, ek, xk, rk, self.Paras)
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())

        # tensor type
        return loss
    

class TR_NoneLower(Optimizer):
    def __init__(self, params, model, hyperparams, Paras):
        defaults = dict()
        super().__init__(params, defaults)
        self.model = model
        self.cutting_num = hyperparams['cutting_number']
        self.M = hyperparams['M']
        self.delta = hyperparams['delta']
        self.Paras = Paras

        self.x_his, self.g_his, self.f_his = [], [], []

    def step(self, closure=None):
        if closure is None:
            raise RuntimeError("Closure required for CuttingPlaneOptimizer")
        
        # Reset the gradient and perform forward computation
        loss = closure()
        
        with torch.no_grad():
            xk = parameters_to_vector(self.model.parameters())
            # print(torch.norm(xk))
            g_k = parameters_to_vector([p.grad if p.grad is not None else torch.zeros_like(p) for p in self.model.parameters()])

            # Add cutting plane
            x_his, f_his, g_his = SPBM_func.add_cutting(self.x_his, self.f_his, self.g_his,xk.detach().clone(), g_k.detach().clone(), loss.detach().clone(), self.cutting_num)

            ## Cut selection
            selected_x, selected_f, selected_g = SPBM_func.cut_selection(x_his, f_his, g_his, self.M)
                    
            # the coefficient of dual problem
            Gk, rk, ek = SPBM_func.get_var(selected_x, selected_f, selected_g, self.delta)
            
            # SOVER (dual)
            xk = SPBM_func.subproblem_tr_NoneLower(Gk, ek, xk, rk, self.Paras)
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())

        # tensor type
        return loss

class TR_NoneCut(Optimizer):
    def __init__(self, params, model, hyperparams, Paras):
        defaults = dict()
        super().__init__(params, defaults)
        self.model = model
        self.cutting_num = hyperparams['cutting_number']
        self.delta = hyperparams['delta']
        self.Paras = Paras

        self.x_his, self.g_his, self.f_his = [], [], []

    def step(self, closure=None):
        if closure is None:
            raise RuntimeError("Closure required for CuttingPlaneOptimizer")
        
        # Reset the gradient and perform forward computation
        loss = closure()
        
        with torch.no_grad():
            xk = parameters_to_vector(self.model.parameters())
            # print(torch.norm(xk))
            g_k = parameters_to_vector([p.grad if p.grad is not None else torch.zeros_like(p) for p in self.model.parameters()])

            # Add cutting plane
            x_his, f_his, g_his = SPBM_func.add_cutting(self.x_his, self.f_his, self.g_his,xk.detach().clone(), g_k.detach().clone(), loss.detach().clone(), self.cutting_num)

            # ## Cut selection
            # selected_x, selected_f, selected_g = SPBM_func.cut_selection(x_his, f_his, g_his, self.M)
                    
            # the coefficient of dual problem
            Gk, rk, ek = SPBM_func.get_var(x_his, f_his, g_his, self.delta)
            
            # SOVER (dual)
            # xk = SPBM_func.subproblem_tr_NoneLower(Gk, ek, xk, rk, self.Paras)

            xk = SPBM_func.subproblem_tr_2(Gk, ek, xk, rk, self.Paras)
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())

        # tensor type
        return loss
    
# ************************** SPBM-PF **************************
class PF_NoneLower(Optimizer):
    def __init__(self, params, model, hyperparams, Paras):
        defaults = dict()
        super().__init__(params, defaults)
        self.model = model
        self.cutting_num = hyperparams['cutting_number']
        self.M = hyperparams['M']
        self.delta = hyperparams['delta']
        self.Paras = Paras

        self.x_his, self.g_his, self.f_his = [], [], []

    def step(self, closure=None):
        if closure is None:
            raise RuntimeError("Closure required for CuttingPlaneOptimizer")
        
        # Reset the gradient and perform forward computation
        loss = closure()
        
        with torch.no_grad():
            xk = parameters_to_vector(self.model.parameters())
            # print(torch.norm(xk))
            g_k = parameters_to_vector([p.grad if p.grad is not None else torch.zeros_like(p) for p in self.model.parameters()])

            # Add cutting plane
            x_his, f_his, g_his = SPBM_func.add_cutting(self.x_his, self.f_his, self.g_his,xk.detach().clone(), g_k.detach().clone(), loss.detach().clone(), self.cutting_num)

            ## Cut selection
            selected_x, selected_f, selected_g = SPBM_func.cut_selection(x_his, f_his, g_his, self.M)
                    
            # the coefficient of dual problem
            Gk, rk, ek = SPBM_func.get_var(selected_x, selected_f, selected_g, self.delta)
            
            # SOVER (dual)
            xk = SPBM_func.subproblem_pf_NoneLower(Gk, ek, xk, self.delta, self.Paras)
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())

        # tensor type
        return loss
    

class PF_NoneCut(Optimizer):
    def __init__(self, params, model, hyperparams, Paras):
        defaults = dict()
        super().__init__(params, defaults)
        self.model = model
        self.cutting_num = hyperparams['cutting_number']
        self.delta = hyperparams['delta']
        self.Paras = Paras

        self.x_his, self.g_his, self.f_his = [], [], []

    def step(self, closure=None):
        if closure is None:
            raise RuntimeError("Closure required for CuttingPlaneOptimizer")
        
        # Reset the gradient and perform forward computation
        loss = closure()
        
        with torch.no_grad():
            xk = parameters_to_vector(self.model.parameters())
            # print(torch.norm(xk))
            g_k = parameters_to_vector([p.grad if p.grad is not None else torch.zeros_like(p) for p in self.model.parameters()])

            # Add cutting plane
            x_his, f_his, g_his = SPBM_func.add_cutting(self.x_his, self.f_his, self.g_his,xk.detach().clone(), g_k.detach().clone(), loss.detach().clone(), self.cutting_num)

            # ## Cut selection
            # selected_x, selected_f, selected_g = SPBM_func.cut_selection(x_his, f_his, g_his, self.M)
                    
            # the coefficient of dual problem
            Gk, rk, ek = SPBM_func.get_var(x_his, f_his, g_his, self.delta)
            
            # SOVER (dual)
            # xk = SPBM_func.subproblem_pf_NoneLower(Gk, ek, xk, self.delta, self.Paras)

            xk = SPBM_func.subproblem_pf(Gk, ek, xk, self.delta, self.Paras)
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())

        # tensor type
        return loss

