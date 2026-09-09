import copy
import unittest
from unittest.mock import patch, AsyncMock
from types import SimpleNamespace
from model import FIELDS
from guidance import ADVICE, impact
import device

class Transport(unittest.IsolatedAsyncioTestCase):
    async def test_scan_filters_and_keeps_exact_address(self):
        from meshcore.ble_cx import UART_SERVICE_UUID
        def pair(address, name, uuids):
            return (SimpleNamespace(address=address,name=name),SimpleNamespace(local_name=name,service_uuids=uuids))
        found={'a':pair('AA:01','MeshCore Test',[]),'b':pair('BB:02','Renamed',[UART_SERVICE_UUID.lower()]),'c':pair('CC:03','Unrelated',[])}
        with patch('bleak.BleakScanner.discover',AsyncMock(return_value=found)):
            self.assertEqual(await device.bluetooth_devices(), [('ble:AA:01','MeshCore Test'),('ble:BB:02','Renamed')])

    async def test_ble_connection_is_closed_after_failure(self):
        connection=SimpleNamespace(disconnect=AsyncMock())
        mc=SimpleNamespace(connect=AsyncMock(side_effect=RuntimeError('connection failed')),disconnect=AsyncMock())
        action=AsyncMock()
        with patch.object(device,'make_connection',return_value=connection),patch('meshcore.MeshCore',return_value=mc):
            with self.assertRaisesRegex(RuntimeError,'Bluetooth connection failed'):
                await device.operate('ble:AA:BB',action)
        action.assert_not_awaited()
        connection.disconnect.assert_awaited_once()

    def test_transport_routing(self):
        with patch('meshcore.BLEConnection') as ble:
            device.make_connection('ble:AA:BB')
            ble.assert_called_once_with(address='AA:BB',pin=True)
        with patch('serial_connection.ClosingSerialConnection') as serial:
            device.make_connection('COM4')
            serial.assert_called_once_with('COM4',115200)

    def test_recommendation_coverage_and_relative_cost(self):
        self.assertEqual(set(ADVICE),set(FIELDS))
        self.assertLess(impact('tx_power','10'),impact('tx_power','22'))
        self.assertLess(impact('spreading_factor','7'),impact('spreading_factor','12'))
        self.assertLess(impact('bandwidth','125'),impact('bandwidth','31.25'))
        self.assertIsNone(impact('name','Tracker'))

class ChannelsUI(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from app import App
        from test_configurator import BASE
        try: self.root=tk.Tk()
        except tk.TclError as exc: self.skipTest(str(exc))
        with patch('app.serial_ports',return_value=[]): self.app=App(self.root)
        self.addCleanup(self.app.close)
        self.addCleanup(setattr,self.app,'pending_count',0)
        s=copy.deepcopy(BASE)
        s['device']['max_channels']=40
        s['channels']=[{'index':i,'name':'Team' if i==0 else '', 'secret':'00'*16} for i in range(40)]
        self.app.show(s)
        self.root.update()

    def visible(self):
        return [i for i,widgets in self.app.channel_widgets.items() if widgets[0].winfo_manager()=='grid']

    def test_add_count_and_keep_edits_when_reduced(self):
        self.assertEqual(self.visible(),[0])
        self.app.channel_count.set('3')
        self.assertEqual(self.visible(),[0,1,2,3])
        self.app.channel_vars[2][0].set('New team')
        self.assertEqual(self.visible(),[0,1,2,3])
        self.app.channel_count.set('0')
        self.assertEqual(self.visible(),[0,2])
        self.assertEqual(self.app.desired_channels()[2]['name'],'New team')

    def test_imported_edit_beyond_visible_slots_is_shown(self):
        self.app.channel_vars[30][0].set('Imported')
        self.assertIn(30,self.visible())

    def test_smallest_window_fits_and_hints_disable(self):
        self.root.geometry('1100x800');self.root.update()
        editor=self.app.entries['multi_acks'].master
        self.assertGreaterEqual(editor.winfo_height(),editor.winfo_reqheight())
        self.assertGreaterEqual(editor.winfo_width(),editor.winfo_reqwidth())
        self.assertTrue(self.app.action_buttons['Review & apply'].winfo_ismapped())
        self.assertTrue(self.app.entries['gps_interval'].instate(['disabled']))

if __name__=='__main__': unittest.main()
