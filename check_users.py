
from neo4j_client import driver
with driver.session() as s:
    r = s.run('MATCH (u:User) WHERE NOT u.user_id STARTS WITH \'agent_\' RETURN u.user_id AS uid, u.risk_score AS score')
    for x in r:
        print(x['uid'], x['score'])

