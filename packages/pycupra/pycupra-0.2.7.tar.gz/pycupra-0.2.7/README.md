# PyCupra

A library to read and send vehicle data via Cupra/Seat portal using the same API calls as the MyCupra/MySeat mobile app.

Fork of https://github.com/Farfar/seatconnect which in turn is a fork of:
Fork of https://github.com/lendy007/skodaconnect which in turn is a fork of:
https://github.com/robinostlund/volkswagencarnet

## Information

Retrieve statistics about your Cupra/Seat from the Cupra/Seat Connect online service

No licence, public domain, no guarantees, feel free to use for anything. Please contribute improvements/bugfixes etc.

## Breaking changes

- The method vehicle.update(updateType) supports 3 different update types: 
   - updateType=0: Small update (=only get_basiccardata() and get_statusreport are called). If the last full update is more than 1100 seconds ago, then a full update is performed.
   - updateType=1: Full update (nearly all get-methods are called. The model images and the capabilitites are refreshed only every 2 hours.)
   - updateType=2: Like updateType=0, but ignoring the nightly update reduction

- Nightly update reduction: If nightly reduction is activated and the current time is within the time frame between 22:00 and 05:00, then vehicle.update(0) performs a full update, if the last full update is more than 1700 seconds ago. If that's not the case, vehicle.update(0) does nothing.

- PyCupra can ask the Seat/Cupra portal to send push notifications to PyCupra if the charging status or the climatisation status has changed or when the API has finished a request like lock or unlock vehicle, start or stop charging or change departure timers or ....

## Thanks to

- [RobinostLund](https://github.com/robinostlund/volkswagencarnet) for initial project for Volkswagen Carnet I was able to fork
- [Farfar](https://github.com/Farfar) for modifications related to electric engines
- [tanelvakker](https://github.com/tanelvakker) for modifications related to correct SPIN handling for various actions and using correct URLs also for MY2021
- [sdb9696](https://github.com/sdb9696) for the firebase-messaging package that is used in PyCupra with only minor modifications

### Example

For an extensive example, please use the code found in example/PyCupra.py.
When logged in the library will automatically create a vehicle object for every car registered to the account. Initially no data is fetched at all. Use the doLogin method and it will sign in with the credentials used for the class constructor. After a successful login, the tokens are stored in a json file. Later doLogin calls can use the token file instead of the credentials.
Method get_vehicles will fetch vehicle basic information and create Vehicle class objects for all associated vehicles in account.
To update all available data use the update_all method of the Connect class. This will call the update function for all registered vehicles, which in turn will fetch data from all available API endpoints.

The file *pycupra_credentials.json.demo* explains the data structure of the credentials file. 


