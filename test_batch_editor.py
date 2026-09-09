import copy
import tkinter as tk
import unittest
from unittest.mock import patch
from batch import plan_many
from test_profiles_batch import radio

class IndividualPlans(unittest.TestCase):
    def test_common_settings_and_separate_names(self):
        plans=plan_many([radio('COM4','a'),radio('COM5','b')],{'settings':{'bandwidth':125}},
                        {'a':{'name':'Tracker-01'},'b':{'name':'Tracker-02'}})
        self.assertEqual(plans[0]['settings'],{'bandwidth':125,'name':'Tracker-01'})
        self.assertEqual(plans[1]['settings'],{'bandwidth':125,'name':'Tracker-02'})

    def test_missing_duplicate_and_invalid_override_block(self):
        snapshots=[radio('COM4','a'),radio('COM5','b')]
        for individual in [{'a':{'name':'One'}},
                           {'a':{'name':'One'},'b':{'name':' one '}},
                           {'a':{'name':'One','private_key':'x'},'b':{'name':'Two'}},
                           {'a':{'name':'One','bandwidth':125},'b':{'name':'Two'}}]:
            with self.subTest(individual=individual),self.assertRaises(ValueError):
                plan_many(snapshots,{'settings':{}},individual)

    def test_coordinates_override_only_their_target(self):
        plans=plan_many([radio('COM4','a'),radio('COM5','b')],{'settings':{}},
                        {'a':{'name':'One','latitude':10},'b':{'name':'Two'}})
        self.assertEqual(plans[0]['settings']['latitude'],10)
        self.assertNotIn('latitude',plans[1]['settings'])

class WizardUI(unittest.TestCase):
    def setUp(self):
        from app import App
        from batch_ui import BatchWindow
        try:self.root=tk.Tk()
        except tk.TclError as exc:self.skipTest(str(exc))
        with patch('app.serial_ports',return_value=[]):self.app=App(self.root)
        with patch('batch_ui.serial_ports',return_value=[('COM4','One'),('COM5','Two')]):self.owner=BatchWindow(self.app)
        self.addCleanup(self.app.close)
        self.owner.snapshots={'COM4':radio('COM4','a'),'COM5':radio('COM5','b')}
        self.owner.select_all();self.root.update()

    def test_numbering_cycles_into_review_without_writes(self):
        from batch_editor import IndividualWizard
        self.owner.document['settings']={'bandwidth':125}
        with patch('batch.apply_device') as writer:
            w=IndividualWizard(self.owner,self.owner.selected_snapshots())
            w.prefix.set('Fleet');w.number();self.assertEqual(w.name.get(),'Fleet-01')
            w.move(1);self.assertEqual(w.name.get(),'Fleet-02')
            w.move(1);self.root.update()
            self.assertEqual([p['settings']['name'] for p in self.owner.plans],['Fleet-01','Fleet-02'])
            writer.assert_not_called()

    def test_cancel_discards_unique_draft(self):
        from batch_editor import IndividualWizard
        w=IndividualWizard(self.owner,self.owner.selected_snapshots())
        w.name.set('Pending');w.move(1);w.close()
        self.assertEqual(self.owner.individual,{})
        self.assertIsNone(self.owner.plans)

    def test_shared_only_supported_fields_and_channel_choice(self):
        from batch_editor import SharedEditor
        self.owner.snapshots['COM4']['settings']['gps_interval']=60
        w=SharedEditor(self.owner,self.owner.selected_snapshots())
        self.assertFalse(w.include['gps_interval'].get())
        self.assertNotIn('name',w.include)
        w.values['bandwidth'].set('125')
        with patch.object(self.owner,'individual_step') as next_step:
            w.save();next_step.assert_called_once()
        self.assertEqual(self.owner.document['settings']['bandwidth'],125)
        self.assertEqual(self.owner.document['channels'],[])

if __name__=='__main__':unittest.main()
