# More info: https://flask.palletsprojects.com/en/2.0.x/quickstart/

# In CLI flask first time running commands in current project folder 

  # Install Python virtualenv package

    pip install virtualenv

  # Activate enviroment variables
    
    virtualenv generateweighins
  
  # Activate the enviroment proposed

    generateweighins\Scripts\activate #PowerShell

  # Install the Flask micro-framework (only if it is your first time)

    pip install Flask
    pip install Flask-MQTT
    pip install Flask-Cors
    pip install -U scikit-learn

  # Set development state in the venv

   ## Windows:
      set FLASK_ENV=development
      set AUTHLIB_INSECURE_TRANSPORT=true

   ## Linux:
      export FLASK_ENV=development 
      export AUTHLIB_INSECURE_TRANSPORT=true

  # Run with host machine IP

    flask run --host=0.0.0.0 --port=5000

  # Some CrateDB SQL Query test
    
    SELECT "time_index","weight_id","point_c1","point_c2","point_c3","point_c4","point_c5","point_c6","point_c7","point_c8","serialn_c1","serialn_c2","serialn_c3","serialn_c4","serialn_c5","serialn_c6","serialn_c7","serialn_c8","weight_c1","weight_c2","weight_c3","weight_c4","weight_c5","weight_c6","weight_c7","weight_c8","voltage_c1","voltage_c2","voltage_c3","voltage_c4","voltage_c5","voltage_c6","voltage_c7","voltage_c8" FROM "mtnewest"."etdsx" ORDER BY "time_index" ASC limit 10000;
     

