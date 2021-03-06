import argparse

#from coffea import hist, processor
#from coffea.analysis_objects import JaggedCandidateArray
from awkward.array.jagged import JaggedArray
import numpy as np
import math

def lepton_selection(leps, cuts, year):

	passes_eta = (np.abs(leps.eta) < cuts["eta"])
	passes_subleading_pt = (leps.pt > cuts["subleading_pt"])
	passes_leading_pt = (leps.pt > cuts["leading_pt"][year])

	if cuts["type"] == "el":
		sca = np.abs(leps.deltaEtaSC + leps.eta)
		passes_id = (leps.cutBased >= 4)
		passes_SC = np.invert((sca >= 1.4442) & (sca <= 1.5660))
		# cuts taken from: https://twiki.cern.ch/twiki/bin/view/CMS/CutBasedElectronIdentificationRun2#Working_points_for_92X_and_later
		passes_impact = ((leps.dz < 0.10) & (sca <= 1.479)) | ((leps.dz < 0.20) & (sca > 1.479)) | ((leps.dxy < 0.05) & (sca <= 1.479)) | ((leps.dxy < 0.1) & (sca > 1.479))

		#select electrons
		good_leps = passes_eta & passes_leading_pt & passes_id & passes_SC & passes_impact
		veto_leps = passes_eta & passes_subleading_pt & np.invert(good_leps) & passes_id & passes_SC & passes_impact

	elif cuts["type"] == "mu":
		passes_leading_iso = (leps.pfRelIso04_all < cuts["leading_iso"])
		passes_subleading_iso = (leps.pfRelIso04_all < cuts["subleading_iso"])
		passes_id = (leps.tightId == 1)

		#select muons
		good_leps = passes_eta & passes_leading_pt & passes_leading_iso & passes_id
		veto_leps = passes_eta & passes_subleading_pt & passes_subleading_iso & passes_id & np.invert(good_leps)

	return good_leps, veto_leps

def calc_dr2(pairs):
	deta = pairs.i0.eta - pairs.i1.eta
	dphi = pairs.i0.phi - pairs.i1.phi
	
	return deta**2 + dphi**2

def calc_dr(objects1, objects2):

	pairs = objects1.p4.cross(objects2.p4)

	return np.sqrt(calc_dr2(pairs))

def pass_dr(pairs, dr):

	return calc_dr2(pairs) > dr**2

"""
def pass_dr(pairs, dr):

	deta = pairs.i0.eta - pairs.i1.eta
	dphi = pairs.i0.phi - pairs.i1.phi
	
	return deta**2 + dphi**2 > dr**2
"""

def jet_selection(jets, leps, mask_leps, cuts):

	nested_mask = jets.p4.match(leps.p4[mask_leps], matchfunc=pass_dr, dr=cuts["dr"])
	# Only jets that are more distant than dr to ALL leptons are tagged as good jets
	jets_pass_dr = nested_mask.all()
	good_jets = (jets.pt > cuts["pt"]) & (np.abs(jets.eta) < cuts["eta"]) & (jets.jetId >= cuts["jetId"]) & jets_pass_dr
	
	if cuts["type"] == "jet":
		good_jets = good_jets & ( (jets.pt < 50) & (jets.puId >= cuts["puId"]) ) | (jets.pt >= 50)

	return good_jets

def jet_nohiggs_selection(jets, fatjets, mask_fatjets, dr=1.2):
	
	nested_mask = jets.p4.match(fatjets.p4[mask_fatjets,0], matchfunc=pass_dr, dr=dr)
	jets_pass_dr = nested_mask.all()

	return jets_pass_dr

"""
def get_leading_mask(mask_events, mask_objects):
	
	mask_leading = mask_objects[:,0]
	
	return mask_events & mask_leading
"""

def get_leading_value(objects, var, mask_events, mask_objects):

	good_objects = objects[mask_objects]
	nobjects = good_objects.counts
	leading_values = -999.9*np.ones_like(nobjects)
	mask_nonzero = mask_events & nobjects > 0
	leading_values[mask_nonzero] = good_objects[var][mask_nonzero][:,0]

	return leading_values
