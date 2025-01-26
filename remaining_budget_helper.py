import requests
import pandas as pd
import numpy as np

def get_distance_and_duration(origin:str, destination:str, api_key:str, commute_type:str):
    """
    Get the distance/duration/fare from two `orgin` and `destination` by `commute_type`.
    """
    # Define the endpoint URL
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    
    # Set up the parameters for the API request
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": commute_type,  # Use 'driving' for driving directions, 'transit'
        "arrival_time":1738170000, # 2025-01-29 09:00 AM
        "key": api_key
    }
    
    # Make the GET request to the API
    response = requests.get(url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        # Check if the response contains valid data
        if data['status'] == 'OK':
            # Extract the distance and duration
            element = data['rows'][0]['elements'][0]
            if 'distance' not in element.keys():
                distance = None
                duration = None
                fare = None
            else:
                distance = element['distance']['value']
                duration = element['duration']['value']
                fare = element.get('fare', {}).get('value', None)  # in the currency's smallest unit
            return distance, duration, fare
        else:
            return None, f"Error: {data['status']}"
    else:
        return None, f"HTTP Error: {response.status_code}"


def get_trans_details(df:pd.DataFrame, commute_type:str, loc_type:str, destination:str, api_key:str)->pd.DataFrame:
    '''
    Get all transportation information from apartments to `destination` by `communte_type`
    '''
    df_copy = df.copy()
    curr_locs = list(map(lambda x: f"{x['latitude']},{x['longitude']}" , df[['latitude', 'longitude']].to_dict('records')))
    res = list(map(lambda x : get_distance_and_duration(x, destination, api_key, commute_type=commute_type), curr_locs))
    
    dist = []
    duration = []
    cost = []
    for i in range(len(res)):
        dist.append(res[i][0])
        duration.append(res[i][1])
        cost.append(res[i][2])

    if commute_type == 'driving':
        df_copy[f'{loc_type}_trans_dist_car'], df_copy[f'{loc_type}_trans_duration_car'], df_copy[f'{loc_type}_trans_cost_car'] = dist, duration, cost
    else:
        df_copy[f'{loc_type}_trans_dist_transit'], df_copy[f'{loc_type}_trans_duration_transit'], df_copy[f'{loc_type}_trans_cost_transit'] = dist, duration, cost

    return df_copy

def filter(df:pd.DataFrame, park:int, hospital:int, grocery:int, cafe:int, min_safety_pr:int)->pd.DataFrame:
    '''
    Filter out useless apartments
    '''
    df_copy = df.copy()
    df_copy = df_copy[df_copy['safety_pr']>=min_safety_pr]

    if park>0:
        df_copy = df_copy[df_copy['nearest_park'].notna()]
    
    # if hospital>0:
    #     df_copy = df_copy[df_copy['hospital'].notna()]

    if grocery>0:
        df_copy = df_copy[df_copy['nearest_supermarket'].notna()]
    
    # if cafe>0:
    #     df_copy = df_copy[df_copy['cafe'].notna()]
        
    return df_copy

def rb(df:pd.DataFrame, car:bool, income:int, budget:int, park:int
       , hospital:int, grocery:int, cafe:int, loc1:int, loc2:int
       , car_cost:int=500, loc1_days_per_month:int=22, loc2_days_per_month:int=8):
    '''
    Find the recommendation apartments based on the formula :
    Remaining Budget = Budget - Rent_price - Communte_cost(or a maintaining cost for a car) - Commute_time * earning_per_min
    '''
    
    df_copy = df.copy()
    df_copy['rb'] = budget - df_copy['price']
    earning_per_min = income / (52 * 40 * 60)

    if car:
        # Maintaining cost for car 
        df_copy['rb'] -= car_cost

        if loc1>0:
            df_copy['rb'] -= df_copy['office_trans_duration_car'] / 60 * earning_per_min * loc1_days_per_month * 2

        if loc2>0:
            df_copy['rb'] -= df_copy['school_trans_duration_car'] / 60 * earning_per_min * loc2_days_per_month * 2
        
        if park>0:
            # All facilities are in walking distances
            df_copy['rb'] -= df_copy['nearest_park_seconds'] / 60 * earning_per_min * park * 2 
        
        # df_copy['rb'] -= df_copy['hospital_trans_duration_transit'] / 60 * earning_per_min * hospital * 2
        if grocery>0:
            df_copy['rb'] -= df_copy['supermarket_duration_seconds'] / 60 * earning_per_min * grocery * 2
        
        # df_copy['rb'] -= df_copy['cafe_trans_duration_transit'] / 60 * earning_per_min * cafe  * 2

    else:
        if loc1>0:
            df_copy['rb'] -= np.where(df_copy['office_trans_cost_transit'].isnull(), 130, df_copy['office_trans_cost_transit'] * loc1_days_per_month * 2)
            df_copy['rb'] -= df_copy['office_trans_duration_transit'] / 60 * earning_per_min * loc1_days_per_month * 2

        if loc2>0:
            df_copy['rb'] -= np.where(df_copy['school_trans_cost_transit'].isnull(), 50, df_copy['school_trans_cost_transit'] * loc1_days_per_month * 2)
            df_copy['rb'] -= df_copy['school_trans_duration_transit'] / 60 * earning_per_min * loc2_days_per_month * 2

        if park>0:
            df_copy['rb'] -= df_copy['nearest_park_seconds'] / 60 * earning_per_min * park * 2
        
        # if hospital:
            # df_copy['rb'] -= df_copy['hospital_trans_duration_transit'] / 60 * earning_per_min * hospital * 2 

        if grocery>0:
            df_copy['rb'] -= df_copy['supermarket_duration_seconds'] / 60 * earning_per_min * grocery * 2
        
        # if cafe:
            # df_copy['rb'] -= df_copy['cafe_trans_duration_transit'] / 60 * earning_per_min * cafe * 2 

    df_copy = df_copy.sort_values('rb', ascending=False).iloc[:5]
    print(df_copy.shape)
    return df_copy[['latLong', 'address', 'nearest_park', 'nearest_supermarket']]


if __name__ == '__main__':
    
    # Parameters
    min_budget = int(input('min_budget'))
    max_budget = int(input('max_budget'))
    park = 2 if True else 0
    hospital = 1 if True else 0
    grocery = 4 if True else 0
    cafe = 4 if True else 0
    min_safety_pr = int(input('min_safety_pr'))
    commute_type = input('commute_type')
    income = int(input('Income')) * 1000
    beds = int(input('beds'))
    api_key = "AIzaSyBNRW3LnHcoCCnXrnRzTCmB73tyYEYw5lM"
    
    # Read data
    df = pd.read_csv('data/df_final_final.csv')
    df = df[df['price']<=max_budget]
    df = df[df['beds'] >= beds]
    df = filter(df=df, park=park, hospital=hospital, grocery=grocery, cafe=cafe, min_safety_pr=min_safety_pr)

    # Calculte transportation details for the loc1
    loc1 = input('loc1').strip()
    if (loc1 != 'Amazon') & (len(loc1)>0):
        loc1.split(',')
        loc1_latitude, loc1_longitude = float(loc1[0].strip()), float(loc1[1].strip())
        destination = f"{loc1_latitude},{loc1_longitude}"
        df = get_trans_details(df=df, commute_type=commute_type, loc_type='office', destination=destination, api_key=api_key)

     # Calculte transportation details for the loc2
    loc2 = input('loc2').strip()
    if (loc2 != 'UW MSDS') & (len(loc2)>0):
        loc2.split(',')
        loc2_latitude, loc2_longitude = float(loc2[0].strip()), float(loc2[1].strip())
        destination = f"{loc2_latitude},{loc2_longitude}"
        df = get_trans_details(df=df, commute_type=commute_type, loc_type='school', destination=destination, api_key=api_key)

    car = commute_type == 'driving'
    remcommend_df = rb(df, car=car, budget=max_budget, income=income, park=park, hospital=hospital
                       , grocery=grocery, cafe=cafe, loc1=len(loc1), loc2=len(loc2), car_cost=500
                       , loc1_days_per_month=22, loc2_days_per_month=8)
    print(remcommend_df)