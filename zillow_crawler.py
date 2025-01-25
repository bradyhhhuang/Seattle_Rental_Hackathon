import pyzill
import json
import pandas as pd
import time 

if __name__ == '__main__':
    ## SLU
    # ne_lat, ne_long = 47.63594831479346, -122.32395276736062
    # sw_lat, sw_long = 47.61859601337818, -122.35010308311078

    ## Capitol Hill
    # ne_lat, ne_long = 47.6393056462584, -122.3144182345458
    # sw_lat, sw_long = 47.612580271954236, -122.33098355711732

    ## University Distrist
    # ne_lat, ne_long = 47.66856061732245, -122.29038564178181
    # sw_lat, sw_long = 47.63676096137662, -122.32961026593767

    ## Queen Anne
    # ne_lat, ne_long = 47.65634789985383, -122.34046245381721
    # sw_lat, sw_long = 47.61746754846293, -122.37629866279416

    ## Downtown
    # ne_lat, ne_long = 47.61880629609206, -122.31639712426501
    # sw_lat, sw_long = 47.59427000863933, -122.36497729304996

    ## Wallingford & Freemont
    ne_lat, ne_long = 47.67276719159568, -122.32159496454409
    sw_lat, sw_long = 47.65299745782093, -122.37592578935127

    pagination = 1
    #pagination is for the list that you see at the right when searching
    #you don't need to iterate over all the pages because zillow sends the whole data on mapresults at once on the first page
    #however the maximum result zillow returns is 500, so if mapResults is 500
    #try playing with the zoom or moving the coordinates, pagination won't help because you will always get at maximum 500 results
    pagination = 10
    proxy_url = None
    zoom = 15
    df = pd.DataFrame()
    for p in range(pagination):
        
        page  = 1 + p
        print(f'scraped page: {page}')

        results_rent = pyzill.for_rent(pagination=page, 
                search_value="seattle",
                min_beds=1, max_beds=None,
                min_bathrooms=None,max_bathrooms=None,
                min_price=None,max_price=None,
                ne_lat=ne_lat,ne_long=ne_long,sw_lat=sw_lat,sw_long=sw_long,
                zoom_value=zoom,
                proxy_url=proxy_url)
        
        jsondata_rent = json.dumps(results_rent)
        jsondata_rent = json.loads(jsondata_rent)
        df_temp = pd.DataFrame(jsondata_rent['listResults'])
        print('list', df_temp.shape)

        df = pd.concat([df, df_temp], axis=0)
        if page == 1:
            df_map = pd.DataFrame(jsondata_rent['mapResults'])
        
        time.sleep(2)
    
    print('map', df_map.shape)
    # df = df[~df.duplicated()]
    df.to_csv('WF_listResults.csv', index=False)
    df_map.to_csv('WF_mapResults.csv', index=False)