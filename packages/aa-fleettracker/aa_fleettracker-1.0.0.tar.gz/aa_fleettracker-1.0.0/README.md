# Fleettracker Plugin App for Alliance Auth (GitHub Version)<a name="example-plugin-app-for-alliance-auth-github-version"></a>

This is an Fleettracker Plugin app for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth)

______________________________________________________________________

<!-- mdformat-toc start --slug=github --maxlevel=6 --minlevel=1 -->

- [Fleettracker Plugin App for Alliance Auth (GitHub Version)](#example-plugin-app-for-alliance-auth-github-version)
  - [Features](#features)
  - [Writing Unit Tests](#writing-unit-tests)
  - [Installing Into Your Dev AA](#installing-into-your-dev-aa)
  - [Setup Permissions](#setup-permissions)


<!-- mdformat-toc end -->

______________________________________________________________________

## Features<a name="features"></a>

- The plugin can save fleet snapshots with optional names
- Fleet detail panel with sorting by corp
- Saves characters and their ships into db


## Installing Into Your Dev AA<a name="installing-into-your-dev-aa"></a>

Once you've cloned or copied all files into place and finished renaming the app,
you're ready to install it to your dev AA instance.

Make sure you're in your venv. Then install it with pip in editable mode:

```bash
pip install aa-fleettracker
```

Add `'fleettracker',` to
INSTALLED_APPS in `settings/local.py`.


```bash
python manage.py migrate
```

Finally, restart your AA server and that's it.

## Setup Permissions<a name="setup-permissions"></a>

Now it's time to set up access permissions for fleettracker module.

| ID                   | Description                       | Notes                                                                                                       |
| :------------------- | :-------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| `basic_access` | Can access module | Anyone that can see previous fleets need that permission |
| `take_snapshot`      | Can take snapshot                 | Everyone with this permission can take new snapshot                                                      |