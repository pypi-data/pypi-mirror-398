from abc import ABC, abstractmethod
import datetime
import time
import os
import random
import torch

from imagejenerator.config import config


class ImageGenerator(ABC):
    """
    Abstract base class for image generation pipelines using PyTorch.

    This class handles the boilerplate for device detection, data type management,
    random seed generation, image saving, and performance logging. Subclasses
    must implement the actual pipeline creation and execution logic.

    Attributes:
        config (dict): Configuration dictionary containing model parameters, paths, and settings.
        device (str): The device being used ('cuda' or 'cpu').
        dtype (torch.dtype): The tensor data type (e.g., torch.float16, torch.bfloat16).
        seeds (list[int]): List of random seeds used for generation.
        generators (list[torch.Generator]): List of PyTorch generators initialized with seeds.
        images (list): List of generated image objects (usually PIL.Image).
    """

    def __init__(self, config = config):
        """
        Initializes the ImageGenerator with a configuration.

        Args:
            config (dict): A dictionary containing configuration parameters.
                Expected keys include:
                - 'device': 'detect', 'cuda', or 'cpu'.
                - 'dtype': 'detect', 'bfloat16', 'float16', or 'float32'.
                - 'seeds': List of integers or None.
                - 'prompts': List of prompt strings.
                - 'images_to_generate': Int, number of images per prompt.
                - 'image_save_folder': Path to save output images.
        """
        self.DTYPES_MAP = {
            "bfloat16": torch.bfloat16,
            "float16": torch.float16,
            "float32": torch.float32,
        }
        self.config = config
        self.pipe = None
        self.images = None
        self.save_timestamp = None
        self.prompts = []
        self.dtype = None
        self.device = None
        self.seeds = config["seeds"]
        self.generators = []
        self.filenames = []
        self.batch = self.config["prompts"] * self.config["images_to_generate"]
        self.batch_size = len(self.config["prompts"]) * self.config["images_to_generate"]
        self.detect_device_and_dtype()
        self.create_generators()


    def detect_device_and_dtype(self):
        """
        If 'device' or 'dtype' in config are set to "detect", this method attempts
        to choose the optimal settings based on hardware availability (e.g., CUDA).
        """
        if self.config["device"] == "detect":
            self.set_device()
        else:
            self.device = self.config["device"]

        self.set_dtype()
        

    def set_device(self):
        """
        Sets the computation device based on CUDA availability.

        Sets `self.device` to 'cuda' if available, otherwise defaults to 'cpu'.
        """
        if torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"


    def set_dtype(self):
        """
        Sets the torch data type based on the device and configuration.

        If config['dtype'] is "detect":
            - Sets to torch.bfloat16 if device is 'cuda'.
            - Sets to torch.float32 otherwise.
        Otherwise, maps the string config to the actual torch.dtype object in self.DTYPES_MAP.
        """
        if self.config["dtype"] == "detect":
            if self.device == "cuda":
                self.dtype = torch.bfloat16
                self.config["dtype"] = "bfloat16"
            else:
                self.dtype = torch.float32
                self.config["dtype"] = "float32"
            return
        
        self.dtype = self.DTYPES_MAP[self.config["dtype"]]


    def create_generators(self):
        """
        Initializes random seeds and PyTorch Generators.

        If seeds are not provided in the config, random seeds are generated
        for the total batch size (number of prompts * images per prompt).
        Populates `self.generators` with `torch.Generator` objects.
        """
        if not self.seeds:
            self.seeds = [self.create_random_seed() for i in range(self.batch_size)]
                
        self.generators = [
            torch.Generator(device=self.device).manual_seed(seed)
            for seed in self.seeds
        ]


    @staticmethod
    def create_random_seed(size: int = 32) -> int:
        """
        Generates a random integer to serve as a seed.

        Args:
            size (int, optional): The bit-size for the random range. Defaults to 32.

        Returns:
            int: A random integer in the range [0, 2**size - 1].
        """
        return random.randint(0, (2**size) - 1)


    @abstractmethod
    def create_pipeline(self):
        """
        Abstract method to initialize the model pipeline.
        
        Subclasses must implement this to load the specific model (e.g., Stable Diffusion)
        and assign it to `self.pipe`.
        """
        pass


    def run_pipeline(self):
        """
        Executes the pipeline implementation.
        """
        self.run_pipeline_impl()


    @abstractmethod
    def run_pipeline_impl(self):
        """
        Abstract method containing the core generation logic.

        Subclasses must implement this to call the model pipeline and populate `self.images`.
        """
        pass
    

    def generate_image(self):
        """
        Main workflow method to generate and save images.

        Steps:
            1. Creates the pipeline.
            2. Runs the pipeline implementation.
            3. Saves the resulting images to disk.
        """
        self.create_pipeline()
        self.run_pipeline()
        self.save_image()


    def save_image(self):
        """
        Saves generated images to the configured directory.

        Images are saved with a timestamped filename. Updates `self.save_timestamp`.
        """
        self.save_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        for i, image in enumerate(self.images):
            file_name = f"{self.save_timestamp}_no{i}.jpg"
            self.filenames.append(file_name)
            save_path = os.path.join(self.config["image_save_folder"], file_name)
            image.save(save_path)


    def get_metadata(self):

        metadata = []
        for i in range(self.batch_size):
            metadata.append({
                "filename": self.filenames[i],
                "save_path": self.config["image_save_folder"],
                "timestamp": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
                "model": self.config["model"],
                "device": self.device,
                "dtype": self.config["dtype"],
                "prompt": self.prompts[i],
                "seed": self.seeds[i],
                "height": self.config["height"],
                "width": self.config["width"],
                "inf_steps": self.config["num_inference_steps"],
                "guidance_scale": self.config["guidance_scale"],
            })
        
        return metadata
