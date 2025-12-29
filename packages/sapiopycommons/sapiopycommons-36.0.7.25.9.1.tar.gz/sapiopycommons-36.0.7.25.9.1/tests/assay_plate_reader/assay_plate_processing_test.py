import unittest

from sapiopylib.rest.User import SapioUser

from sapiopycommons.files.assay_plate_reader import AssayPlateReader, ProcessAssayPlateRequest, AssayFileLoadResult, \
    AssayResultDatum

user = SapioUser(url="https://linux-vm:8443/webservice/api", verify_ssl_cert=False,
                 guid="66c2bea5-7cb2-4bfc-a413-304a3f4c3f33",
                 username="yqiao_api", password="Password1!")
processor = AssayPlateReader(user)

class AssayPlateReaderProcessingTest(unittest.TestCase):
    def test_bmg_labtech_96(self):
        """
        This is just start of some tests. The more rig test is in sapio-commons java unit tests, per default config instead of just 1 config on a little bit of canary test.
        """
        file_data: bytes
        with open("BMGLabtech96.txt", "rb") as file:
            file_data = file.read()
        file_load_result: AssayFileLoadResult = processor.process_plate_reader_data(ProcessAssayPlateRequest(8, 12, None, "BMGLabtech96.txt", file_data, "BMG Labtech"))
        self.assertEqual(len(file_load_result.plateResultList), 2)
        plates = file_load_result.plateResultList
        # Find the plate that is labelled "Raw Data (355-20/455-30 1)" as channel.
        plate = next((p for p in plates if p.resultIdent and p.resultIdent.channelIdOrBlock == "Raw Data (355-20/455-30 1)"), None)
        self.assertIsNotNone(plate)
        # The plate should have plate ID "140205_HeLa-CCR5"
        self.assertEqual(plate.resultIdent.plateId, "140205_HeLa-CCR5")
        # Value of A1 should be 1
        a1_read = next((d for d in plate.resultDatum if d.rowPosition == "A" and d.columnPosition == "1"), None)
        self.assertIsNotNone(a1_read)
        self.assertEqual(a1_read.valueByPropertyName.get(AssayResultDatum.DEFAULT_PROPERTY_NAME), 1)
        # Value of H12 should be 12
        h12_read = next((d for d in plate.resultDatum if d.rowPosition == "H" and d.columnPosition == "12"), None)
        self.assertIsNotNone(h12_read)
        self.assertEqual(h12_read.valueByPropertyName.get(AssayResultDatum.DEFAULT_PROPERTY_NAME), 12)
        # Find the plate labelled "Raw Data (610-30/675-50 2)"
        plate = next((p for p in plates if p.resultIdent and p.resultIdent.channelIdOrBlock == "Raw Data (610-30/675-50 2)"), None)
        self.assertIsNotNone(plate)
        # The plate should have plate ID "140205_HeLa-CCR5"
        self.assertEqual(plate.resultIdent.plateId, "140205_HeLa-CCR5")


