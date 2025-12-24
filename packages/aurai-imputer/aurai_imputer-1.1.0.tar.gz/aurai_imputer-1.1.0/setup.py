from setuptools import setup, find_packages

setup(
    name='aurai_imputer',
    version='1.1.0',
    author='Abdul Mofique Siddiqui',
    author_email='mofique7860@gmail.com',
    description='AURAI: A uniquely hybrid imputation model that unifies mask-aware variational autoencoding, latent-neighbor correction, and adaptive feature gating to deliver uncertainty-aware reconstruction of missing data.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Luckyy0311',
    license='MIT',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    python_requires='>=3.8',
    install_requires=[
        'numpy>=1.20',
        'pandas>=1.0',
        'torch>=1.10',
        'scikit-learn>=1.0'
    ],
)