from setuptools import setup, find_packages

setup(
    name="synapse_ai_tools",  
    version="0.3.2",  
    description="A Python package for artificial intelligence development, providing utilities for machine learning, deep learning, data processing, and model deployment.",  
    long_description=open('README.md').read(),  
    long_description_content_type="text/markdown",  
    author="SYNAPSE AI SAS",  
    author_email="servicios@groupsynapseai.com",  
    # url="",  
    packages=find_packages(),  
    install_requires=[  
        "matplotlib",  
        "seaborn",     
        "pandas",
        "numpy<2.0",
        "librosa",
        "pydot",
        "tensorflow==2.10",
        "scikit-learn",    
        "pillow"       
    ],
    classifiers=[  
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6, <3.11', 
    include_package_data=True,
    package_data={
    'synapse_ai.DNN': ['src/*.ico', 'src/*.png'],
    }
)