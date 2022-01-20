FROM tensorflow/serving:latest-devel
MAINTAINER "Rio McMahon" <rmcmahon@ucar.edu>

# there are two options for deploying a model:
#   1. use a script to generate the model from scratch (used as an example
#      to avoid repo overhead of storing model weights)
#   2. saving in the model weights directly into the `/tfc/user_model/`
#      folder. 
# both options are presented below. Uncomment/comment the option as desired.

# OPTION 1
# create dummy model using simple script
COPY /tfc/etc/build_dummy_model.py /
RUN python /build_dummy_model.py

# OPTION 2
# copy in a pre-saved model into `/tfc/user_model/`
# the files saved into `/tfc/user_model/` should be the output from
# the keras function `model.save()` (output for simple model will include
# assets, saved_model.pb, variables, keras_metadata.pb) - save it all
# into the `/tfc/user_model/` folder.
# COPY /tfc/user_model/ /models/model/1
