# Property Info Rewriting using Ollama and Django

## Overview

This Django project is designed to generate new titles, descriptions, and summaries for properties using the Ollama gemma2 model. The project fetches existing property data from a PostgreSQL database, generates new content using a local instance of the Ollama model, and stores the results back in the database. It includes a custom management command that processes all properties in the database, updating their titles, descriptions, and summaries using AI-generated content.

## Features

- Rewrite property titles and descriptions using AI
- Generate property summaries based on updated information
- Batch process all properties in the database
- Error handling and logging for robust execution

## Prerequisites

- Python 3.x
- Django
- Ollama API running locally (default URL: http://localhost:11434)
- PostgreSQL
- SQLAlchemy
- dotenv (highly recommended for database confidentiality)
- Virtualenv (optional but recommended)

## Project Structure

***Make sure that ollama_django/ and django/ are in the same directory.***

```bash
root/
├── ollama_django/
│   ├── property_summary_project/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── summary_app/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── generate_property_info.py
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── views.py
│   ├── .env
│   ├── .gitignore
│   ├── manage.py
│   ├── requirements.txt
│   └── README.md
│
└── django/
    └── property_app/    # The external Django app being integrated
        ├── models.py
        └── ...
    
```

## Key Files and Directories

- property_app/: Django app for managing property models
- summary_app/: Django app for managing summary models
- management/commands/generate_property_info.py: Custom management command for property rewriting

## Setup Instructions

  1. **Clone the repository**:
  
      ```bash
      git clone https://github.com/nafiahossain/ollama_django.git
      cd ollama_django
      ```

  2. **Create and activate a virtual environment** (optional but recommended):
  
      Create a virtual environment and install dependencies:
      
      ```bash
      python3 -m venv venv
      source venv/bin/activate  # On Windows use `venv\Scripts\activate`
      ```

  3. **Install dependencies**:

     First, install the necessary dependencies to run the Django project. You can do this by running one of the following commands: 

      ```bash
      pip install -r requirements.txt
      ```
      
      or,
     
      ```bash
      pip install django psycopg2-binary sqlalchemy python-dotenv requests
      ```

     Next, ensure that you have Ollama installed on your system. Ollama is required for running the gemma2 model, which is used in this project. To verify if Ollama is installed, run the following command:

      ```bash
      ollama --version
      ```
      
      If you see a version number, Ollama is installed. If you encounter a "command not found" error, then you need to install Ollama from [here](https://ollama.com/)!

      **If Ollama and your desired LLaMA model are already installed, you can skip this part.** Otherwise, once Ollama is installed, you need to run the model. For this project, we use the gemma2 model with 2 billion parameters. To run it, use the following command:
     
      ```bash
      ollama run gemma2:2b
      ```

     Please note that it may take around 25-30 minutes to load and run the model.

     
  4. **Set up Cinfigurations and environment variables**:
  
      Ensure you have a .env (rename the .env.sample to .env, then add your credentials) file at the root of the Django project containing the following:
      
      ```env
      SECRET_KEY=your-secret-key

      DB_NAME=yourdatabase
      DB_USER=username
      DB_PASSWORD=password
      DB_HOST=localhost
      DB_PORT=5433
      ```

      **You can use the previously created database for the Django project to store the data migrated through this django project. So, no need to create a new database.**
      Ensure that your PostgreSQL server is running, and the database specified in the .env file exists.

     Rename the config.py.sample to config.py. This config file include the `Property` model import from the `property_app` application's model. It also include the Ollama API url. The Ollama API URL is set to http://localhost:11434/api/generate by default. Modify the ollama_url variable in the `config.py` if your setup differs.

     ```python
     #config.py

     from property_app.models import Property

     OLLAMA_API_URL = 'http://localhost:11434/api/generate'
     ```
     
  6. **Integrating `property_app` from Another Django Project**

     This project (ollama_django) utilizes the property_app from a different Django project located in the same directory (as shown in the [Project Structure](#project-structure)). Below are the steps and considerations for setting this up:

     1. Add `property_app` to the `INSTALLED_APPS` in ollama_django/property_summary_project/settings.py.py:

        ```python
        # property_summary_project/settings.py.py

        # Application definition

        INSTALLED_APPS = [
            'summary_app',
            'property_app',
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
        ]
        ```

     2. Ensure Python Can Locate `property_app`:

        Since `property_app` resides in a different Django project within the same parent directory, adjust the sys.path in settings.py to include the path to `property_app`:

        ```python
        # property_summary_project/settings.py.py
        
        import os
        import sys

        # Add the path to property_app
        sys.path.append('../django')
        ```

        To examine that the path defined in sys.path.append is correct, you can check this in python shell this way:

        ```bash
        python manage.py shell
        ```
        Then in the shell:

        ```python
        from property_app.models import Property  # Import the Property model
        Property.objects.all()  # Query all Property instances
        ```

        If you see no error, then the path definition is correct.
        
     4. Reference `property_app` Models:

        When using models from `property_app`, you can import them directly in your code:

        ```python
        from property_app.models import Property
        ```
     
     5. Handle Migrations:

        When running migrations for `ollama_django`, ensure that any migrations related to `property_app` are applied correctly. You may need to manually run migrations in the `property_app` directory or include them in your workflow.

  7. **Run migrations**:
  
      Apply the database migrations, this will create the Summary model:
      
      ```bash
      python manage.py makemigrations property_app
      python manage.py migrate
      ```

  8. **Property rewriting command**:
  
      Before running this command, make sure to keep the previous django folder and the ollama_django folder in the same directory (as shown in the [Project Structure](#project-structure)).
     
      If the scrapy image directory setup is done, then run this command to migrate data from the existing scrapy database:

     ```bash
      python manage.py generate_property_info
      ```

      This command will:

        1. Fetch all properties from the database
        2. Rewrite each property's title and description using the Ollama API
        3. Generate a summary for each property
        4. Update the database with the new information

  9. **Create an admin user** (Optional):
  
      To use the admin panel, First you’ll need to create a user who can login to the admin site. Run the following command:
        
      ```bash
      python manage.py createsuperuser
      ```
    
      Enter your desired username, email address, and password. You will be asked to enter your password twice, the second time as a confirmation of the first. Using this info, you can log in to the admin panel and       perform CRUD operation on the migrated data.

  10. **Run the development server**:
  
      Start the Django development server:
      
      ```bash
      python manage.py runserver
      ```
    
      Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to see the application. To perfrom CRUD operation on data, you'll need to log in to the admin panel which is [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/). 

   - Output:

        - Database: AI Generated data stored in 'yourdatabase', in the PostgreSQL database.
        - Django Admin Interface: AI Generated data can be seen on the admin interface.


## Usage

  - **Admin Interface**: Access the Django admin at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) to manage properties, locations, amenities, and images.

## Configuration

- The `property_app` app is external to this project, meaning any changes to it should be done carefully to avoid breaking dependencies. Make sure the directory structure remains consistent when deploying or sharing this project.
- The Ollama API URL is set to http://localhost:11434/api/generate by default. Modify the ollama_url variable in the `config.py` if your setup differs.
- The AI model used is "gemma2:2b". You can change this in the generate_ollama method if needed.

## Error Handling
The command includes error handling for:

- API communication issues
- Content parsing errors
- Database update failures

Errors are logged to the console for debugging purposes.

## Testing

After running the server, check the [Django admin interface](http://127.0.0.1:8000/admin/) to view all the migrated data. There will be three models, Properties, Amenities, and Locations. You can perform CRUD operations on these models. Also check your database and image directory whether the data was migrated or not. 

## Disclaimer
This project uses AI to generate content. Always review and verify the AI-generated content before using it in a production environment.

## License
This project is licensed under the MIT License - see the [LICENSE](https://github.com/nafiahossain/ollama_django/LICENSE) file for details.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
