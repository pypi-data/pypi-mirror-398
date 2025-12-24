
# X.YaN   # Alpha release
# X.YbN   # Beta release
# X.YrcN  # Release Candidate
# X.Y     # Final release
# x.y.dev

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="krazy",
    version="0.23.05",
    author="Kartik",
    author_email="kartik@live.com",
    description="My own small package of uitilities I use.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kartikjain11/krazy",
    project_urls={
        "Bug Tracker": "https://github.com/kartikjain11/krazy/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "krazy"},
    # packages=setuptools.find_packages(where="krazy"),
    packages=setuptools.find_namespace_packages(where="krazy"),
    python_requires=">=3.9.5",
    install_requires=['pandas','openpyxl','pathlib','pytesseract','gspread','oauth2client',
                      'pyodbc','sqlalchemy','configparser','scikit-learn','chardet', 
                      'langchain', 'langchain_community','langchain_experimental',
                      'crewai', 'crewai[tools]','fastapi','uvicorn','torch'],
)
