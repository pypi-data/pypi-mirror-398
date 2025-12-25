#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2023
#

from setuptools import setup, find_packages
from sciveo.version import __version__

extras_require = {
      'mon': [
        'psutil>=0.0.0',
      ],
      'net': [
        'netifaces>=0.0.0',
        'scapy>=0.0.0',
      ],
      'server': [
        'fastapi>=0.0.0',
        'uvicorn[standard]>=0.0.0',
        'flask>=0.0.0',
        'waitress>=0.0.0',
      ],
      'media': [
        'scikit-learn>=0.0.0', 'scipy>=0.0.0', 'scikit-video>=0.0.0', 'scikit-image>=0.0.0', 'pycryptodome>=0.0.0', 'exifread>=0.0.0', 'qrcode[pil]>=0.0.0',
        'boto3', 'pandas>=0.0.0', 'pika>=0.0.0', 'regex>=0.0.0', 'matplotlib>=0.0.0', 'joblib>=0.0.0', 'tqdm>=0.0.0', 'mss>=0.0.0',
        'ffmpeg-python>=0.0.0', 'opencv-python-headless>=0.0.0', 'opencv-contrib-python-headless>=0.0.0',
      ],
      'media-ml': [
        'tensorflow>=0.0.0', 'keras>=0.0.0',
        'torch>=0.0.0', 'torchvision>=0.0.0',
        'diffusers>=0.0.0', 'transformers>=0.0.0', 'sentence_transformers>=0.0.0', 'accelerate>=0.0.0', 'annoy>=0.0.0',
        'ultralytics>=0.0.0'
      ],
      'web': [
        'django>=0.0.0',
        'djangorestframework>=0.0.0',
        'django-allauth>=0.0.0',
      ],
      'db': [
        'pandas>=0.0.0',
        'psycopg2>=0.0.0',
        'pyarrow>=0.0.0'
      ],
      'power': [
        'pymodbus>=0.0.0',
      ]
}

extras_require['all'] = extras_require['mon'] + extras_require['net'] + extras_require['server']
extras_require['ml'] = extras_require['all'] + extras_require['media'] + extras_require['media-ml']

setup(
    name='sciveo',
    version=__version__,
    packages=find_packages(),
    install_requires=[
      'numpy>=0.0.0',
      'requests>=0.0.0',
    ],
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    extras_require=extras_require,
    py_modules=['sciveo'],
    entry_points={
      'console_scripts': [
        'sciveo=sciveo.cli:main',
      ],
    },
)
