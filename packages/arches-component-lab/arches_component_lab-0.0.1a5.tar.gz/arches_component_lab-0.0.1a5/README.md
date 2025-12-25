# Welcome to Arches Component Lab!

Arches Component Lab is an experimental collection components that can be used to build custom applications on top of the Arches platform. It includes a set data management components and services designed for working with Arches data in Vue 3 and PrimeVue.

Please see the [project page](http://archesproject.org/) for more information on the Arches project.


## Installation

If you are installing Arches Component Lab for the first time, we strongly recommend that you install it as an Arches application into a existing (or new) project. Running Arches Component Lab as a standalone project can provide some convenience if you are a developer contributing to the Arches Component Lab project but you risk conflicts when upgrading to the next version of Arches Component Lab.

Install Arches Component Lab using the following command:
```
pip install arches-component-lab
```

For developer install instructions, see the [Developer Setup](#developer-setup-for-contributing-to-the-arches-component-lab-project) section below.


## Project Configuration

1. If you don't already have an Arches project, you'll need to create one by following the instructions in the Arches [documentation](http://archesproject.org/documentation/).

2. When your project is ready, add "arches_querysets", "arches_component_lab" to INSTALLED_APPS **below** the name of your project. 
For projects using Arches >= 8.x also add "pgtrigger" as follows:
```python
    INSTALLED_APPS = (
        ...
        "my_project_name",
        "arches_querysets",
        "arches_component_lab",
        "pgtrigger",             # Only when using Arches >= 8.x
    )
    ```

3. Next ensure arches and arches_component_lab are included as dependencies in package.json
    ```
    "dependencies": {
        "arches": "archesproject/arches#dev/8.0.x",
        "arches_component_lab": "archesproject/arches-component-lab#main"
    }
    ```

4. Update urls.py to include the arches_component_lab urls
    ```
    urlpatterns = [
        path("", include("arches_component_lab.urls")),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    ```

5. Start your project
    ```
    python manage.py runserver
    ```

6. Next cd into your project's app directory (the one with package.json) install and build front-end dependencies:
    ```
    npm install
    npm run build_development
    ```

## Developer Setup (for contributing to the Arches Component Lab project)

1. Download the arches-component-lab repo:

    a.  If using the [Github CLI](https://cli.github.com/): `gh repo clone archesproject/arches-component-lab`
    
    b.  If not using the Github CLI: `git clone https://github.com/archesproject/arches-component-lab.git`

2. Download the arches package:

    a.  If using the [Github CLI](https://cli.github.com/): `gh repo clone archesproject/arches`

    b.  If not using the Github CLI: `git clone https://github.com/archesproject/arches.git`

3. Create a virtual environment outside of both repositories: 
    ```
    python3 -m venv ENV
    ```

4. Activate the virtual enviroment in your terminal:
    ```
    source ENV/bin/activate
    ```

5. Navigate to the `arches-component-lab` directory, and install the project (with development dependencies):
    ```
    cd arches-component-lab
    pip install -e . --group dev
    ```

6. Also install core arches for local development:
    ```
    pip install -e ../arches
    ```


7. Run the Django server:
    ```
    python manage.py runserver
    ```

8.  (From the `arches-component-lab` top-level directory) install the frontend dependencies:
    ```
    npm install
    ```

9.  Once the dependencies have been installed, generate the static asset bundle:

    a. If you're planning on editing HTML/CSS/JavaScript files, run `npm start`. This will start a development server that will automatically detect changes to static assets and rebuild the bundle.

    b. If you're not planning on editing HTML/CSS/JavaScript files, run `npm run build_development`

10. If you ran `npm start` in the previous step, you will need to open a new terminal window and activate the virtual environment in the new terminal window. If you ran `npm run build_development` then you can skip this step.

11. Setup the database:
    ```
    python manage.py setup_db
    ```

12. In the terminal window that is running the Django server, halt the server and restart it.
    ```
    (ctrl+c to halt the server)
    python manage.py runserver
    ```

## Committing changes

NOTE: Changes are committed to the arches-component-lab repository. 

1. Navigate to the repository
    ```
    cd arches-component-lab
    ```

2. Cut a new git branch
    ```
    git checkout origin/main -b my-descriptive-branch-name
    ```

3. If updating models or branches

    1. Manually export the model or branch from the project

    2. Manually move the exported model or branch into one of the subdirectories in the `arches-component-lab/arches_component_lab/pkg/graphs` directory.

4. Add your changes to the current git commit
    ```
    git status
    git add -- path/to/file path/to/second/file
    git commit -m "Descriptive commit message"
    ```

5. Update the remote repository with your commits:
    ```
    git push origin HEAD
    ```

6. Navigate to https://github.com/archesproject/arches-component-lab/pulls to see and commit the pull request