from setuptools import setup, find_packages
from pathlib import Path

# Determine long_description from available README files (prefer Markdown)
this_directory = Path(__file__).parent
long_description_text = None
for candidate_name in [
    "README.md",
    "DOCUMENTATION_CONSOLIDATION_SUMMARY.md",
    "MARKDOWN_CONSOLIDATION_PLAN.md",
]:
    candidate_path = this_directory / candidate_name
    if candidate_path.exists():
        long_description_text = candidate_path.read_text(encoding="utf-8")
        break

if long_description_text is None:
    long_description_text = """
    # Project Overview: MediCafe

    ## Project Description
    MediCafe is a comprehensive suite designed to automate and streamline several aspects of medical administrative tasks within Medisoft, a popular medical practice management software. The system consists of two main components: MediBot and MediLink, each serving distinct functions but integrated to enhance the workflow of medical practices.

    ## MediBot Module
    MediBot is primarily focused on automating data entry processes in Medisoft. It utilizes AutoHotkey scripting to control and automate the GUI interactions required for inputting patient data into Medisoft. Key features and functionalities include:

    - **Error Handling and Logging:** MediBot aims to implement a robust error handling mechanism that can log issues and provide feedback for troubleshooting.
    - **Insurance Mode Adjustments:** The system can adjust data inputs based on specific requirements from various insurance providers, including Medicare.
    - **Diagnosis Entry Automation:** MediBot automates the extraction and entry of diagnosis codes from surgical schedules into Medisoft.
    - **Script Efficiency:** The module enhances the efficiency of scripts handling Medisoft's quirks, such as fields that are skipped or require special navigation.
    - **User Interface (UI) Enhancements:** Plans to develop a graphical user interface to help non-technical users manage and execute scripts more easily.
    - **Documentation and Support:** Comprehensive documentation and support channels are being established to assist users in setup, configuration, and troubleshooting.

    ## MediLink Module
    MediLink focuses on the backend processes related to medical claims submission, particularly handling communications with multiple endpoints like Availity, Optum, and PNT Data. Its main features include:

    - **Dynamic Configurations:** Supports multiple endpoints with environmental settings to ensure flexibility in claims submission.
    - **File Detection and Integrity Checks:** Enhances the detection of new claim files with detailed logging and integrity checks for preprocessing validation.
    - **Automated Response Handling:** Automates the process of receiving and integrating response files from endpoints into Medisoft, alerting users to exceptions.
    - **Endpoint Management:** Allows dynamic updating of endpoints based on insurance provider changes, ensuring accurate and efficient claims processing.
    - **User Interface (UI) Interactions:** Provides a user interface for managing claims submission, including confirming or adjusting suggested endpoints.

    ## Integration and Workflow
    The two modules work in tandem to provide a seamless experience. MediBot handles the initial data entry into Medisoft, preparing the system with up-to-date patient and treatment information. This data is then utilized by MediLink for preparing and submitting medical claims to various insurance providers. Errors and feedback from MediLink can prompt adjustments in MediBot's data entry processes, creating a feedback loop that enhances accuracy and efficiency.

    The integration aims to reduce the administrative burden on medical practices, decrease the incidence of data entry errors, and ensure timely submission of medical claims, thereby improving the revenue cycle management of healthcare providers.

    ## Target Users
    The system is intended for use by administrative staff in medical practices who are responsible for patient data management and claims processing. By automating these tasks, the system not only saves time but also reduces the potential for human error, leading to more accurate billing and improved operational efficiency.

    ## Future Directions
    Future enhancements may include the development of additional modules for other aspects of medical practice management, further integrations with healthcare systems, and continuous improvements in user interface design to accommodate an even broader range of users.
    """

setup(
    name='medicafe',
    version="0.251227.0",
    description='MediCafe',
    long_description=long_description_text,
    long_description_content_type='text/markdown',
    keywords='medicafe medibot medilink medisoft automation healthcare claims',
    url='https://github.com/katanada2/MediCafe',
    project_urls={
        'Source': 'https://github.com/katanada2/MediCafe',
        'Bug Tracker': 'https://github.com/katanada2/MediCafe/issues',
    },
    author='Daniel Vidaud',
    author_email='daniel@personalizedtransformation.com',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(include=['MediCafe', 'MediCafe.*', 'MediBot', 'MediBot.*', 'MediLink', 'MediLink.*']),
    include_package_data=False,  # Disable automatic inclusion to prevent CSV files from being included
    package_data={
        'MediBot': ['*.bat'],
        'MediLink': ['openssl.cnf', '*.html']
    },
    python_requires='>=3.4, <3.5',
    install_requires=[
        'requests==2.21.0',
        'argparse==1.4.0',
        'numpy==1.11.3; platform_python_implementation != "CPython" or sys_platform != "win32" or python_version > "3.5"',
        'pandas==0.20.0; platform_python_implementation != "CPython" or sys_platform != "win32" or python_version > "3.5"',
        'tqdm==4.14.0',
        'lxml==4.2.0; platform_python_implementation != "CPython" or sys_platform != "win32" or python_version > "3.5"',
        'python-docx==0.8.11',
        'PyYAML==5.2',
        'chardet==3.0.4',
        'cffi==1.8.2', # msal needs this and then pip install will fail because 1.15.X won't work on XP.
        'msal==1.26.0'
    ],
    extras_require={
        'binary': [
            'numpy==1.11.3; platform_python_implementation == "CPython" and sys_platform == "win32" and python_version <= "3.5"',
            'pandas==0.20.0; platform_python_implementation == "CPython" and sys_platform == "win32" and python_version <= "3.5"',
            'lxml==4.2.0; platform_python_implementation == "CPython" and sys_platform == "win32" and python_version <= "3.5"',
        ]
    },
    entry_points={
        'console_scripts': [
            'medicafe=MediCafe.__main__:main',
        ],
    },
    zip_safe=False
)