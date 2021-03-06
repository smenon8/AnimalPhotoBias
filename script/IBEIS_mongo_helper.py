import mongod_helper as mh
import json, logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(filename)s: '    
                            '[%(levelname)s:] '
                            '%(funcName)s(): '
                            '%(lineno)d:\t'
                            '%(message)s')

def PRINT(jsonLike):
    print(json.dumps(jsonLike, indent=4))


# This method is used to generate the gid:aid map
def genGidAidDictFromDB(client, source):
    gid_aid_tbl_obj = mh.mongod_table(client, "ibeis_gid_annot_tab", source)
    res_obj = mh.result_iterator(gid_aid_tbl_obj.query({}, ['aid']))

    gid_aid_map = {gid :res_obj[gid]['aid'] for gid in res_obj.keys()}

    return gid_aid_map

def extractImageFeaturesFromMap(client, feature, source="GZC"):
    aid_ftr_tbl_obj = mh.mongod_table(client, "ibeis_annot_ftr_tab", source)
    res_obj = mh.result_iterator(aid_ftr_tbl_obj.query({}, [feature]))

    PRINT(res_obj)
    gid_aid_map = genGidAidDictFromDB(client, source)

    gid_ftr = {}
    for gid in gid_aid_map.keys():
        if gid_aid_map[gid][0] != None:
            for aid in gid_aid_map[gid][0]:
                if res_obj.get(str(aid), False): # to handle cases where there is an annotation but no feature
                    gid_ftr[gid] = gid_ftr.get(gid, []) + [res_obj[str(aid)][feature]]
                else:
                    print("GID : %s, AID : %s" %(gid, str(aid)))

    # PRINT(res_obj)
    return gid_ftr