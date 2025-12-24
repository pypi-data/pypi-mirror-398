# Fraud Scoring (CatBoost + Isotonic Calibration)

A tiny Python package that predicts a calibrated fraud probability for a single car claim.

## Install
```bash
!pip install fraudet

from fraudet import predict_fraud

pred = predict_fraud(
    AccidentArea="Urban",
    DayOfWeekClaimed="Monday",
    MonthClaimed="Jan",
    Sex="Female",
    MaritalStatus="Single",
    Fault="Third Party",
    VehicleCategory="Sedan",
    VehiclePrice="20000 to 29000",
    DaysPolicyAccident="more than 30",
    DaysPolicyClaim="more than 30",
    PastNumberOfClaims=0,
    AgeOfVehicle="3 years",
    AgeOfPolicyHolder="26 to 30",
    PoliceReportFiled="No",
    WitnessPresent="No",
    AgentType="External",
    NumberOfSuppliments="1 to 2",
    AddressChangeClaim="no change",
    NumberOfCars="1 vehicle",
    BasePolicy="Liability",
)


print(pred.proba_fraud)

