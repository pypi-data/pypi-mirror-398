from setuptools import setup, find_packages


setup(
    name='stewiedev-hello',
    version='0.1',
    packages=['stewiedev_hello'],
    install_requires={
        #Add dependencies here 
        
    },
    entry_points={
        'console_scripts': [
            'stewie=stewiedev_hello.main:hello',
        ]
    }
)