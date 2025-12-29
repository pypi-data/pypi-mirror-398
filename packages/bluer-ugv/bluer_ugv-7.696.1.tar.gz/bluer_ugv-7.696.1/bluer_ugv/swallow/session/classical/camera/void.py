from bluer_ugv.swallow.session.classical.camera.generic import ClassicalCamera


class ClassicalVoidCamera(ClassicalCamera):
    def initialize(self) -> bool:
        return True

    def cleanup(self):
        pass
