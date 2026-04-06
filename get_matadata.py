from raritan import rpc
from raritan.rpc import pdumodel

PDU_IP = "10.0.42.2"
agent = rpc.Agent("https", PDU_IP, "admin", "raritan")
pdu = pdumodel.Pdu("/model/pdu/0", agent)
metadata = pdu.getMetaData()
print(metadata)