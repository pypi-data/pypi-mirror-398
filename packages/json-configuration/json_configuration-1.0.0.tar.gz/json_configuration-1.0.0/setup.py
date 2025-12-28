from setuptools import setup

if __name__ == '__main__':
    setup(
        name = 'json-configuration',
        version = '1.0.0', 
        packages = ['json_configuration'], 
        install_requires = ['pydantic>=2.12.5']
    )