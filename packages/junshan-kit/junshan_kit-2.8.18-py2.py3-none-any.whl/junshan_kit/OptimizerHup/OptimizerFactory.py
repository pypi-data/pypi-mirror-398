from junshan_kit.OptimizerHup import SPBM, SPBM_func
import torch, time, os
from torch.optim.optimizer import Optimizer
from torch.nn.utils import parameters_to_vector, vector_to_parameters


class SPSmax(Optimizer):
    def __init__(self, params, model, hyperparams, Paras):
        defaults = dict()
        super().__init__(params, defaults)
        self.model = model
        self.c = hyperparams['c']
        self.gamma = hyperparams['gamma']
        if 'f_star' not in Paras or Paras['f_star'] is None:
            self.f_star = 0
        else:
            self.f_star = Paras['f_star']
        self.step_size = []

    def step(self, closure=None):
        if closure is None:
            raise RuntimeError("Closure required for SPSmax")
        
        # Reset the gradient and perform forward computation
        loss = closure()
        
        with torch.no_grad():
            xk = parameters_to_vector(self.model.parameters())
            # print(torch.norm(xk))
            g_k = parameters_to_vector([p.grad if p.grad is not None else torch.zeros_like(p) for p in self.model.parameters()])

            # Step-size
            step_size = (loss - self.f_star) / ((self.c * torch.norm(g_k, p=2) ** 2) + 1e-8)
            step_size = min(step_size, self.gamma)
            self.step_size.append(step_size)

            # Update
            xk = xk - step_size * g_k
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())


        # emporarily return loss (tensor type)
        return loss
    

class ALR_SMAG(Optimizer):
    def __init__(self, params, model, hyperparams, Paras):
        defaults = dict()
        super().__init__(params, defaults)
        self.model = model
        self.c = hyperparams['c']
        self.eta_max = hyperparams['eta_max']
        self.beta = hyperparams['beta']
        if 'f_star' not in Paras or Paras['f_star'] is None:
            self.f_star = 0
        else:
            self.f_star = Paras['f_star']
        self.step_size = []
        self.d_k = torch.zeros_like(parameters_to_vector(self.model.parameters()))

    def step(self, closure=None):
        if closure is None:
            raise RuntimeError("Closure required for SPSmax")
        
        # Reset the gradient and perform forward computation
        loss = closure()
        
        with torch.no_grad():
            xk = parameters_to_vector(self.model.parameters())
            # print(torch.norm(xk))
            g_k = parameters_to_vector([p.grad if p.grad is not None else torch.zeros_like(p) for p in self.model.parameters()])

            self.d_k = self.beta * self.d_k + g_k
            # Step-size
            step_size = (loss - self.f_star) / ((self.c * torch.norm(self.d_k, p=2) ** 2) + 1e-8)
            step_size = min(step_size, self.eta_max)
            self.step_size.append(step_size)

            # Update
            xk = xk - step_size * g_k
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())


        # emporarily return loss (tensor type)
        return loss
    

class Bundle(Optimizer):
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

            # the coefficient of dual problem
            Gk, rk, ek = SPBM_func.get_var(x_his, f_his, g_his, self.delta)
            
            # SOVER (dual)
            xk = SPBM_func.bundle(Gk, ek, xk, self.delta, self.Paras)
            
            # print(len(self.f_his))
            vector_to_parameters(xk, self.model.parameters())

        # loss（tensor）
        return loss
    
    