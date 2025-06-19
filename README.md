
# Intelligent System for Fraud Detection in Auto Insurance Policies

This project aims to develop a system based on Machine Learning and Deep Learning models that:\
•	Predicts the likelihood of fraud using structured data.\
•	Classifies the severity of the damage using images.\
•	Identifies damaged auto parts using image segmentation.




## Authors

- Juan José Hurtado Ordoñez
- Rogelio Rivera Meléndez
- Ignacio Sáyago Vela




## Usage

The project runs on 3 different docker containers

     1. Fraud detection endpoint
     2. Severity classification and damage detection endpoint
     3. Front end

\
The files required to build the containers are located in the CONTAINERS folder

First you need to build and deploy containers 1 and 2, either locally or on a cloud platform

Once containers 1 and 2 are running, before building the image for container 3 you have to edit the 'front.py' file located in CONTAINERS\front_streamlit_cloud folder, and insert the URLs of the deployed containers 1 and 2. 

- The url of container 1 must end with "/fraud_detection"

- The url of container 2 must end wiht "/damage_detection"

Then you can build and delpoy container 3 either locally or on a cloud platform.
