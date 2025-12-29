from time import time
import setuptools
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='abstract_database',
    version='0.0.2.110',
    author='putkoff',
    author_email='partners@abstractendeavors.com',
    description="A lightweight' , 'env-driven toolkit for Postgres connections' , 'table helpers' , 'and Pandas exports.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/AbstractEndeavors/abstract_database",

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
    ],
    install_requires=['pillow' , 'abstract_apis' , 'abstract_database' , 'abstract_gui' , 'abstract_math' ,'abstract_pandas' ,
                      'abstract_security' ,'abstract_utilities' ,'numpy' ,'pandas' , 'psycopg2' ,'sqlalchemy', 'abstract_pandas'],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    # Add this line to include wheel format in your distribution
    setup_requires=['wheel'],
)

 
