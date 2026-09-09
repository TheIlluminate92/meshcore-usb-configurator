"""Conservative starting points, separate from user-owned saved profiles."""
import copy

SOURCE = 'https://docs.meshcore.io/cli_commands/'
COMMON = 'Keep the existing local mesh frequency, bandwidth, spreading factor, coding rate and transmit power. Choose a unique name. These are starting points, not MeshCore official recommendations.'
PROFILES = [
 {'id':'builtin-companion', 'name':'Companion — recommended starting point', 'builtin':True, 'target_role':'companion',
  'description':'General messaging companion. Selected discovery keeps contacts manageable; existing contacts are retained. Telemetry is limited to allowed contacts, location sharing is off, and extra acknowledgements are off to avoid extra transmissions. GPS stays as configured. '+COMMON,
  'settings':{'manual_add_contacts':1, 'overwrite_oldest':0, 'auto_add_chat':0, 'auto_add_repeater':1, 'auto_add_room_server':1, 'auto_add_sensor':0,
              'advert_location_policy':0,'telemetry_mode_base':1,'telemetry_mode_loc':0,'telemetry_mode_env':0,'multi_acks':0},
  'channels':[], 'naming':{'prefix':'Companion','start':1}},
 {'id':'builtin-repeater', 'name':'Repeater — setup reference', 'builtin':True, 'target_role':'repeater',
  'description':'Requires Repeater firmware and its CLI. Preview/export reference only in this version; Companion settings cannot turn a radio into a repeater. Conservative fixed-site starting point: forwarding on, infrequent discovery adverts. Use fixed coordinates only after checking the site; choose a unique admin password separately. '+COMMON,
  'settings':{}, 'channels':[], 'naming':{'prefix':'Repeater','start':1}, 'source':SOURCE,
  'cli_settings':{'repeat':'on','advert.interval':120,'flood.advert.interval':24},
  'advice':['repeat on: forwards mesh traffic; energy use depends on traffic.', 'advert.interval 120 minutes: local discovery every two hours; modest periodic airtime.', 'flood.advert.interval 24 hours: daily network discovery; slower discovery, less airtime. Match local operator policy.', 'Keep routing delays, duty-cycle controls, scopes and hash mode unchanged until the local network requirements are known.']},
 {'id':'builtin-room', 'name':'Room Server — setup reference', 'builtin':True, 'target_role':'room',
  'description':'Requires Room Server firmware and its CLI. Preview/export reference only in this version. Dedicated chat room: forwarding off, read-only guest mode off. Choose guest access and a unique admin password separately; never distribute an admin password in a shared profile. '+COMMON,
  'settings':{}, 'channels':[], 'naming':{'prefix':'Room','start':1}, 'source':SOURCE,
  'cli_settings':{'repeat':'off','allow.read.only':'off','advert.interval':120,'flood.advert.interval':24},
  'advice':['repeat off: keeps the room focused on chat rather than forwarding unrelated traffic.', 'allow.read.only off: normal room access policy; review guest access separately.', 'Local adverts every 120 minutes and flood adverts every 24 hours: conservative discovery traffic; match local operator policy.', 'Message traffic and connected clients determine much of the room server airtime and battery demand.']}
]

def entries():
    return copy.deepcopy(PROFILES)
