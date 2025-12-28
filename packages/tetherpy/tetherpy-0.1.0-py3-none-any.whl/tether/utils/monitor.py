import torch
import torch.nn as nn
from typing import Dict, Optional, Any
from ..nn.lif import LIF
from ..nn.alif import ALIF
from ..nn.plif import PLIF

class Monitor:
    """
    Utility for monitoring SNN statistics (firing rates, membrane potentials).
    """
    def __init__(self, model: nn.Module):
        self.model = model

    def get_firing_rates(self) -> Dict[str, float]:
        """
        Retrieve the latest firing rates from all layers that track it (e.g. LIF).
        """
        rates = {}
        for name, module in self.model.named_modules():
            if hasattr(module, "firing_rate"):
                rates[name] = module.firing_rate
        return rates

    def get_voltage_traces(self) -> Dict[str, torch.Tensor]:
        """
        Retrieve voltage traces from LIF layers (requires store_traces=True).
        """
        traces = {}
        for name, module in self.model.named_modules():
            if isinstance(module, (LIF, ALIF, PLIF)) and module.v_seq is not None:
                traces[name] = module.v_seq
        return traces

    def enable_voltage_monitoring(self, enable: bool = True):
        """
        Enable or disable voltage trace storage on all LIF layers.
        """
        for module in self.model.modules():
            if isinstance(module, (LIF, ALIF, PLIF)):
                module.store_traces = enable

    def log_to_tensorboard(self, writer: Any, step: int, prefix: str = "snn"):
        """
        Log firing rates to TensorBoard.
        
        Parameters
        ----------
        writer : torch.utils.tensorboard.SummaryWriter
            TensorBoard writer instance.
        step : int
            Global step.
        prefix : str
            Prefix for tag names.
        """
        rates = self.get_firing_rates()
        for name, rate in rates.items():
            writer.add_scalar(f"{prefix}/firing_rate/{name}", rate, step)

    def log_to_wandb(self, wandb_module: Any, step: int, prefix: str = "snn"):
        """
        Log firing rates to Weights & Biases.

        Parameters
        ----------
        wandb_module : module
            The wandb module (or run object).
        step : int
            Global step.
        prefix : str
            Prefix for metric names.
        """
        rates = self.get_firing_rates()
        log_dict = {f"{prefix}/firing_rate/{name}": rate for name, rate in rates.items()}
        # Handle module vs run object if possible, but standard wandb.log works
        if hasattr(wandb_module, 'log'):
             wandb_module.log(log_dict, step=step)
