from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from a4x.orchestration.utils import StrCompatPathLike, StrCompatPathLikeForIsInstance
from a4x.orchestration.workflow import Workflow


class Plugin(ABC):
    def __init__(self, plugin_name: str, wflow: Workflow):
        """
        Base class constructor for all A4X-Orchestration plugins

        :param plugin_name: the name of the plugin. Used for YAML config keys and certain messages produced by the base class
        :type plugin_name: str
        :param wflow: the workflow to convert to the specific WMS/RJMS associated with the plugin
        :type wflow: a4x.orchestration.workflow.Workflow
        """
        self.plugin_name = plugin_name
        self.a4x_wflow = wflow
        self.plugin_settings_key = f"{self.plugin_name}_plugin"
        self.plugin_settings = (
            self.a4x_wflow.annotations[self.plugin_settings_key]
            if self.plugin_settings_key in self.a4x_wflow.annotations
            else None
        )

    def configure(
        self,
        *args,
        a4x_config_out_file: Optional[StrCompatPathLike] = None,
        **kwargs,
    ):
        """
        Configure the workflow for the given WMS/RJMS

        :param args: positional arguments that are passed through to the plugin child class
        :param a4x_config_out_file: if provided, generate an A4X-Orchestration YAML config at the specified path
        :type a4x_config_out_file: Optional[Union[str, os.PathLike]]
        :param kwargs: keyword arguments that are passed through to the plugin child class
        """
        self.configure_plugin(*args, **kwargs)
        self.plugin_settings = self.create_plugin_settings_for_a4x_config()
        if self.plugin_settings is not None and len(self.plugin_settings) > 0:
            self.a4x_wflow.annotations[f"{self.plugin_name}_plugin"] = (
                self.plugin_settings
            )
        if a4x_config_out_file is not None:
            if not isinstance(a4x_config_out_file, StrCompatPathLikeForIsInstance):
                raise TypeError(
                    "The 'a4x_config_out_file' argument must be a string or a type compliant with os.PathLike"
                )
            self.a4x_wflow.to_config(a4x_config_out_file)

    def get_plugin_settings_from_wflow(self) -> Optional[Dict[str, Any]]:
        """
        Utility function for child classes that extracts plugin settings (i.e.,
        what should be created :code:`create_plugin_settings_for_a4x_config`)
        from the :code:`a4x.orchestration.Workflow` class's annotations

        :return: the plugin settings, if present in :code:`self.a4x_wflow.annotations` or :code:`None` otherwise
        :rtype: Optional[Dict[str, Any]]
        """
        if f"{self.plugin_name}_plugin" not in self.a4x_wflow.annotations:
            return None
        return self.a4x_wflow.annotations[f"{self.plugin_name}_plugin"]

    @abstractmethod
    def execute(self, *args, **kwargs):
        """
        An abstract method implemented by children classes to run the workflow
        under the WMS/RJMS

        :param args: positional arguments defined by the child class
        :param kwargs: keyword arguments defined by the child class
        """
        pass

    @abstractmethod
    def create_plugin_settings_for_a4x_config(self) -> Dict[str, Any]:
        """
        An abstract method implemented by children classes to create a dict
        containing settings needed to reload a configured workflow from an
        A4X-Orchestration YAML config

        :return: a dict containing the plugin settings needed for restoration from an A4X-Orchestration YAML config
        :rtype: Dict[str, Any]
        """
        pass

    @abstractmethod
    def configure_plugin(self, *args, **kwargs):
        """
        An abstract method implemented by children classes to create/configure
        a WMS/RJMS version of the workflow

        This method is automatically called by :code:`self.configure`. Users
        do not need to call this method.

        :param args: positional arguments defined by the child class
        :param kwargs: keyword arguments defined by the child class
        """
        pass
