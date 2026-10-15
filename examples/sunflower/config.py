"""Worked example: tagging config for 'Sunflower Bank Business CC App
02.2026.pdf' — a 2-page InDesign credit-card application form with 95
AcroForm fields and two 'Schumer box' disclosure tables.

Produced output validates as PDF/UA-1 in veraPDF and renders
pixel-identically to the untagged original.

Every y/x number below was read from `opdump.py` output for THIS document.
Do not reuse the numbers for any other file.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from tag_engine import node, table, tr, th, F, M, MC, REST

TITLE = 'Sunflower Bank Visa Business Card Credit Application'
LANG = 'en-US'          # catalog already had it; kept for completeness
PDFUA = True
REMOVE_CIDSET = True    # InDesign wrote incomplete CIDSets (UA 7.21.4.2)

# On page 1 every /C2_0 glyph is a printed ZapfDingbats checkbox square that
# merely duplicates an interactive widget checkbox -> artifact.
# (On page 2, /C2_0 is a regular text font — the rule is page-scoped!)
def ARTIFACT_TEXT(pageno, y, x, font):
    return pageno == 0 and font == '/C2_0'

# Page 2 'Customer Diligence' Yes/No boxes are print-only (no widgets), and
# the font's ToUnicode maps the box glyph to the letter 'r'. Replace each
# with U+2610 BALLOT BOX via an ActualText span.
def ACTUALTEXT(pageno, y, x, font, label):
    if pageno == 1 and font == '/C2_1' and label in ('P_q1', 'P_q2', 'P_q3'):
        return '☐'
    return None

# ---------------------------------------------------------------- bands
# (ymin, ymax, [(xlimit, key), ..., (None, key)]): first rule with x < xlimit
# wins; key None means "no content expected here" (engine errors loudly).
BANDS = {
 0: [
    (24, 44.5, [(360, 'H1'), (None, 'P_btcap')]),
    (44.5, 52, [(360, 'H1'), (490, 'P_bt1'), (None, 'P_bt2')]),
    (52, 62,   [(360, 'P_climreq'), (490, 'P_bt3'), (None, 'P_bt4')]),
    (62, 72,   [(360, 'P_climreq'), (490, 'P_bt5'), (None, 'P_bt6')]),
    (72, 85,   [(360, 'P_climinc'), (None, 'P_bt7')]),
    (88, 99,   [(None, 'P_privacy')]),
    (99, 128,  [(None, 'P_cip')]),
    (130, 140, [(None, 'H2_company')]),
    (140, 160, [(None, 'P_colbl1')]),
    (160, 180, [(None, 'P_colbl2')]),
    (185, 205, [(None, 'P_colbl3')]),
    (213, 222, [(179, 'H2_owner'), (None, 'P_ownnote')]),
    (225, 240, [(None, 'P_owlbl1')]),
    (245, 258, [(None, 'P_owlbl2')]),
    (265, 282, [(None, 'P_owlbl3')]),
    (288, 300, [(None, 'P_owlbl4')]),
    (310, 320, [(None, 'P_owlbl5')]),
    (335, 348, [(410, 'H2_cc'), (None, 'P_ccnote')]),
    (348, 357, [(None, 'P_cclbl')]),
    (357, 372, [(None, 'P_cc1')]),
    (375, 392, [(None, 'P_cc2')]),
    (395, 412, [(None, 'P_cc3')]),
    (425, 436, [(None, 'H2_stmt')]),
    (436, 448, [(None, 'P_choose')]),
    (455, 467, [(410, 'H2_credit'), (None, 'P_crednote')]),
    (467, 480, [(460, 'P_instlbl'), (None, 'P_loanopts')]),
    (485, 502, [(None, 'P_acctlbl')]),
    (508, 520, [(None, 'P_trlbl')]),
    (520, 545, [(None, 'P_tr1')]),
    (545, 565, [(None, 'P_tr2')]),
    (570, 592, [(None, 'P_tr3')]),
    (600, 615, [(410, 'H2_fin'), (None, 'P_finnote')]),
    (615, 630, [(None, 'P_fin1')]),
    (632, 650, [(None, 'P_fin2')]),
    (655, 676, [(327, 'P_finimp'), (None, 'P_networth')]),
    # 'Interest Rates and Interest Charges' Schumer box: 2 columns at x=200
    (678, 692, [(None, 'TH_irhdr')]),
    (692, 716, [(200, 'TH_apr'), (None, 'TD_apr')]),
    (716, 731, [(200, 'TH_cash'), (None, 'TD_cash')]),
    (731, 762, [(200, 'TH_avoid'), (None, 'TD_avoid')]),
    (762, 776, [(200, 'TH_min'), (None, 'TD_min')]),
 ],
 1: [
    # 'Fees' Schumer box: 2 columns at x=199
    (24, 36,   [(None, 'TH_fhdr')]),
    (40, 50.5, [(199, 'TH_annual'), (None, 'TD_annual')]),
    (50.5, 62, [(None, 'TH_trans')]),
    (62, 73,   [(199, 'TH_bal'), (None, 'TD_bal')]),
    (73, 84,   [(199, 'TH_cashf'), (None, 'TD_cashf')]),
    (84, 95,   [(199, 'TH_foreign'), (None, 'TD_foreign')]),
    (95, 106,  [(None, 'TH_penalty')]),
    (106, 117, [(199, 'TH_late'), (None, 'TD_late')]),
    (117, 128, [(199, 'TH_over'), (None, 'TD_over')]),
    (128, 139, [(199, 'TH_ret'), (None, 'TD_ret')]),
    (139, 150, [(None, 'TH_other')]),
    (150, 161, [(199, 'TH_exp'), (None, 'TD_exp')]),
    (161, 172, [(199, 'TH_pay'), (None, 'TD_pay')]),
    (175, 220, [(None, 'P_prime')]),
    (226, 236, [(None, 'H2_reggg')]),
    (236, 256, [(None, 'P_reggg')]),
    (263, 275, [(135, 'H2_dilig'), (None, 'P_dilignote')]),
    (275, 286, [(None, 'P_q1')]),
    (286, 296, [(None, 'P_q2')]),
    (296, 315, [(None, 'P_q3')]),
    (322, 333, [(None, 'H2_sig')]),
    (333, 385, [(None, 'P_pleaseread')]),
    (385, 397, [(None, 'P_authoff')]),
    (400, 414, [(None, 'P_titles')]),
    (420, 430, [(None, 'P_sigx')]),
    (430, 442, [(None, 'P_siglbl')]),
    (446, 456, [(None, 'P_return')]),
    (456, 468, [(None, 'P_accuracy')]),
 ],
}

# ------------------------------------------------------------ field names
# /TU accessible names: what a screen reader announces on each field.
TU = {
 'Credit Limit 1': 'Credit limit requested in dollars (minimum of $10,000.00)',
 'Credit Limit': 'Credit limit increase amount in dollars',
 'Check Box 18': 'Credit limit requested',
 'Check Box 19': 'Credit limit increase',
 'Check Box 1': 'Business type: Closely held corporation',
 'Check Box 2': 'Business type: Partnership',
 'Check Box 3': 'Business type: Publicly held corporation',
 'Check Box 4': 'Business type: Proprietorship',
 'Check Box 5': 'Business type: Limited liability company',
 'Check Box 6': 'Business type: Non-profit organization',
 'Check Box 7': 'Business type: Other',
 'Other': 'Other business type, please specify',
 'Name of Company': 'Name of company',
 'Name of Company 1': 'Tax I.D. number',
 'Company Address': 'Company address',
 'Company city': 'Company city',
 'Company state': 'Company state',
 'Company zip': 'Company ZIP code',
 'Company phone': 'Business phone',
 'Company type': 'Type of business',
 'Company Revenue': 'Gross annual revenue',
 'Company How many years': 'How many years in business',
 'Owner Last Name': 'First principal or owner: last name',
 'Owner First Name 1': 'First principal or owner: first name',
 'Owner Middle Name': 'First principal or owner: middle name',
 'Owner Percentage': 'Percentage of ownership',
 'Owner SS': 'First principal or owner: Social Security number',
 'Owner Title': 'First principal or owner: company title',
 'Owner Income': 'First principal or owner: gross annual income',
 'Owner DOB': 'First principal or owner: date of birth',
 'Owner Address': 'First principal or owner: home address',
 'Owner City': 'First principal or owner: home address city',
 'Owner State': 'First principal or owner: home address state',
 'Owner Zip': 'First principal or owner: home address ZIP code',
 'Owner How long': 'First principal or owner: years at home address',
 'Own or rent': 'First principal or owner: own, rent, or other',
 'Owner Monthly Payment': 'First principal or owner: monthly housing payment',
 'Owner phone': 'First principal or owner: home phone',
 'Owner date': 'First principal or owner: date signed',
 'Institution Name': 'Credit information: institution name and address',
 'Institution Branch': 'Credit information: branch',
 'Institution Loan': 'Credit information: loans',
 'Check Box 10': 'Loans: open',
 'Check Box 11': 'Loans: closed',
 'Institution Account-checking': 'Checking account number and name listed',
 'Institution Account-savings': 'Savings account number and name listed',
 'Check Box 8': 'Statement option: consolidated',
 'Check Box 9': 'Statement option: individual',
 'Current Assets': 'Current assets in dollars',
 'Current Liabilities': 'Current liabilities in dollars',
 'Condensed Bus Total Assets': 'Total assets in dollars',
 'Condensed Bus Total Liabilities': 'Total liabilities in dollars',
 'Condensed Bus Net Worth': 'Net worth in dollars (total assets less liabilities)',
 'Check Box 12': 'Authorized officer title: President or Chairman',
 'Check Box 13': 'Authorized officer title: Vice President',
 'Check Box 14': 'Authorized officer title: Treasurer',
 'Check Box 15': 'Authorized officer title: Owner',
 'Check Box 16': 'Authorized officer title: Partner',
 'Check Box 17': 'Authorized officer title: Managing member',
}
for n in (1, 2, 3):
    TU[f'{n} Bus CC Last name' + ('' if n == 1 else f' {n-1}')] = f'Cardholder {n}: last name'
    TU[f'{n} Bus CC First name {n}'] = f'Cardholder {n}: first name'
    TU[f'{n} Bus CC Middle name' + ('' if n == 1 else f' {n-1}')] = f'Cardholder {n}: middle initial'
    TU[f'{n} Bus CC SS' + ('' if n == 1 else f' {n-1}')] = f'Cardholder {n}: last 4 digits of Social Security number'
    TU[f'{n} Bus CC DOB' + ('' if n == 1 else f' {n-1}')] = f'Cardholder {n}: date of birth'
    TU[f'{n} Bus CC Phone' + ('' if n == 1 else f' {n-1}')] = f'Cardholder {n}: primary phone number'
TU['1 Bus CC Credit'] = 'Cardholder 1: credit limit'
TU['1 Bus CC Credit 1'] = 'Cardholder 2: credit limit'   # row-2 field misnamed in source
TU['3 Bus CC Credit 2'] = 'Cardholder 3: credit limit'
for pfx in ('', '2-', '3-'):
    sfx = {'': '', '2-': ' 1', '3-': ' 2'}[pfx]
    num = {'': 1, '2-': 2, '3-': 3}[pfx]
    TU[f'{pfx}Trade Reference Name{sfx}'] = (
        f'Trade reference {num}: name and address'
        + (' (institution credit card)' if num == 3 else ''))
    TU[f'{pfx}Trade Reference Account name{sfx}'] = f'Trade reference {num}: name under which account is carried'
    TU[f'{pfx}Trade Reference Account number{sfx}'] = f'Trade reference {num}: account number'
    TU[f'{pfx}Trade Reference Account Balance{sfx}'] = f'Trade reference {num}: balance in dollars'
    TU[f'{pfx}Trade Reference Monthly Payment{sfx}'] = f'Trade reference {num}: monthly payment in dollars'

# ------------------------------------------------------------------ tree
# Reading order. Form fields are placed inside the paragraph that holds
# their visible label, in visual order.
TREE = [
 node('H1', M),
 node('P_climreq', F('Check Box 18'), M, F('Credit Limit 1')),
 node('P_climinc', F('Check Box 19'), M, F('Credit Limit')),
 node('P_btcap', M),
 node('P_bt1', F('Check Box 1'), M),
 node('P_bt2', F('Check Box 2'), M),
 node('P_bt3', F('Check Box 3'), M),
 node('P_bt4', F('Check Box 4'), M),
 node('P_bt5', F('Check Box 5'), M),
 node('P_bt6', F('Check Box 6'), M),
 node('P_bt7', F('Check Box 7'), M, F('Other')),
 node('P_privacy', M),
 node('P_cip', M),
 node('H2_company', M),
 node('P_colbl1', M, F('Name of Company'), F('Name of Company 1')),
 node('P_colbl2', M, F('Company Address'), F('Company city'),
      F('Company state'), F('Company zip'), F('Company phone')),
 node('P_colbl3', M, F('Company type'), F('Company Revenue'),
      F('Company How many years')),
 node('H2_owner', M),
 node('P_ownnote', M),
 node('P_owlbl1', M, F('Owner Last Name'), F('Owner First Name 1'),
      F('Owner Middle Name'), F('Owner Percentage'), F('Owner SS')),
 node('P_owlbl2', M, F('Owner Title'), F('Owner Income'), F('Owner DOB')),
 node('P_owlbl3', M, F('Owner Address'), F('Owner City'), F('Owner State'),
      F('Owner Zip'), F('Owner How long')),
 node('P_owlbl4', M, F('Own or rent'), F('Owner Monthly Payment'),
      F('Owner phone')),
 node('P_owlbl5', M, F('Owner date')),
 node('H2_cc', M),
 node('P_ccnote', M),
 node('P_cclbl', M),
 node('P_cc1', M, F('1 Bus CC Last name'), F('1 Bus CC First name 1'),
      F('1 Bus CC Middle name'), F('1 Bus CC SS'), F('1 Bus CC DOB'),
      F('1 Bus CC Phone'), F('1 Bus CC Credit')),
 node('P_cc2', M, F('2 Bus CC Last name 1'), F('2 Bus CC First name 2'),
      F('2 Bus CC Middle name 1'), F('2 Bus CC SS 1'), F('2 Bus CC DOB 1'),
      F('2 Bus CC Phone 1'), F('1 Bus CC Credit 1')),
 node('P_cc3', M, F('3 Bus CC Last name 2'), F('3 Bus CC First name 3'),
      F('3 Bus CC Middle name 2'), F('3 Bus CC SS 2'), F('3 Bus CC DOB 2'),
      F('3 Bus CC Phone 2'), F('3 Bus CC Credit 2')),
 node('H2_stmt', M),
 node('P_choose', MC(0), F('Check Box 8'), MC(1), F('Check Box 9'), MC(2)),
 node('H2_credit', M),
 node('P_crednote', M),
 node('P_instlbl', M, F('Institution Name'), F('Institution Branch'),
      F('Institution Loan')),
 node('P_loanopts', F('Check Box 10'), MC(0), F('Check Box 11'), MC(1)),
 node('P_acctlbl', M, F('Institution Account-checking'),
      F('Institution Account-savings')),
 node('P_trlbl', M),
 node('P_tr1', MC(0), F('Trade Reference Name'),
      F('Trade Reference Account name'), F('Trade Reference Account number'),
      MC(1), F('Trade Reference Account Balance'),
      MC(2), F('Trade Reference Monthly Payment')),
 node('P_tr2', MC(0), F('2-Trade Reference Name 1'),
      F('2-Trade Reference Account name 1'),
      F('2-Trade Reference Account number 1'),
      MC(1), F('2-Trade Reference Account Balance 1'),
      MC(2), F('2-Trade Reference Monthly Payment 1')),
 node('P_tr3', MC(0), F('3-Trade Reference Name 2'),
      F('3-Trade Reference Account name 2'),
      F('3-Trade Reference Account number 2'),
      MC(1), F('3-Trade Reference Account Balance 2'),
      MC(2), F('3-Trade Reference Monthly Payment 2')),
 node('H2_fin', M),
 node('P_finnote', M),
 node('P_fin1', MC(0), F('Current Assets'), MC(1), F('Current Liabilities')),
 node('P_fin2', MC(0), F('Condensed Bus Total Assets'), REST,
      F('Condensed Bus Total Liabilities')),
 node('P_finimp', M),
 node('P_networth', M, F('Condensed Bus Net Worth')),
 table('Table_ir',
       tr('TR_ir0', th('TH_irhdr', 'Column', colspan=2)),
       tr('TR_ir1', th('TH_apr', 'Row'), node('TD_apr', M)),
       tr('TR_ir2', th('TH_cash', 'Row'), node('TD_cash', M)),
       tr('TR_ir3', th('TH_avoid', 'Row'), node('TD_avoid', M)),
       tr('TR_ir4', th('TH_min', 'Row'), node('TD_min', M))),
 table('Table_fees',
       tr('TR_f0', th('TH_fhdr', 'Column', colspan=2)),
       tr('TR_f1', th('TH_annual', 'Row'), node('TD_annual', M)),
       tr('TR_f2', th('TH_trans', 'Both', colspan=2)),
       tr('TR_f3', th('TH_bal', 'Row'), node('TD_bal', M)),
       tr('TR_f4', th('TH_cashf', 'Row'), node('TD_cashf', M)),
       tr('TR_f5', th('TH_foreign', 'Row'), node('TD_foreign', M)),
       tr('TR_f6', th('TH_penalty', 'Both', colspan=2)),
       tr('TR_f7', th('TH_late', 'Row'), node('TD_late', M)),
       tr('TR_f8', th('TH_over', 'Row'), node('TD_over', M)),
       tr('TR_f9', th('TH_ret', 'Row'), node('TD_ret', M)),
       tr('TR_f10', th('TH_other', 'Both', colspan=2)),
       tr('TR_f11', th('TH_exp', 'Row'), node('TD_exp', M)),
       tr('TR_f12', th('TH_pay', 'Row'), node('TD_pay', M))),
 node('P_prime', M),
 node('H2_reggg', M),
 node('P_reggg', M),
 node('H2_dilig', M),
 node('P_dilignote', M),
 node('P_q1', M),
 node('P_q2', M),
 node('P_q3', M),
 node('H2_sig', M),
 node('P_pleaseread', M),
 node('P_authoff', M),
 node('P_titles', M, F('Check Box 12'), F('Check Box 13'), F('Check Box 14'),
      F('Check Box 15'), F('Check Box 16'), F('Check Box 17')),
 node('P_sigx', M),
 node('P_siglbl', M),
 node('P_return', M),
 node('P_accuracy', M),
]
