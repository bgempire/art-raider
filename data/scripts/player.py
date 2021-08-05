import bge

from bge.types import *
from mathutils import Vector
from .bgf import DEBUG


PLAYER_MOV_SPEED = 0.05
PLAYER_CAMERA_SLOW_PARENT = 60.0
PLAYER_CAMERA_FORWARD = 2
PLAYER_CAMERA_DISTANCE = 0
PLAYER_DEFAULT_PROPS = {
    "Direction" : "R",
    "Moving" : False,
    "Action" : "",
}
PLAYER_ANIMS = {
    "Idle" : (0, 59),
    "Walk" : (70, 89),
    "Use" : (100, 115),
}


def main(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    
    if not own.groupObject:
        own.endObject()
        return
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            own.scene.active_camera = own.childrenRecursive["Camera"]
            own.scene.active_camera.timeOffset = PLAYER_CAMERA_SLOW_PARENT
            initPlayer(cont)
            
        setProps(cont)
        processAnimation(cont)
        processMovement(cont)


def initPlayer(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    for prop in PLAYER_DEFAULT_PROPS.keys():
        own[prop] = PLAYER_DEFAULT_PROPS[prop]
        if DEBUG: own.addDebugProperty(prop)


def setProps(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    keyUp = bge.logic.keyboard.events[bge.events.WKEY] == 1
    keyDown = bge.logic.keyboard.events[bge.events.SKEY] == 2
    keyLeft = bge.logic.keyboard.events[bge.events.AKEY] == 2
    keyRight = bge.logic.keyboard.events[bge.events.DKEY] == 2
    
    if not own["Action"] and keyUp:
        own["Action"] = "Use"
    
    elif keyLeft and not keyRight:
        own["Direction"] = "L"
        own["Moving"] = True
        
    elif not keyLeft and keyRight:
        own["Direction"] = "R"
        own["Moving"] = True
        
    elif not keyLeft and not keyRight or keyLeft and keyRight or own["Action"]:
        own["Moving"] = False
        

def processAnimation(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    armature = own.childrenRecursive["PlayerArmature"] # type: BL_ArmatureObject
    
    animation = "Idle"
    
    if not own["Action"]:
        
        if own["Moving"]:
            animation = "Walk"
        
        # Invert armature direction
        if own["Direction"] == "L":
            armature.localScale.x = -1
        else:
            armature.localScale.x = 1
            
    elif own["Action"] == "Use":
        actionFrame = int(armature.getActionFrame())
        frameThreshold = int(PLAYER_ANIMS["Use"][1])
        
        if actionFrame >= frameThreshold-2 and actionFrame <= frameThreshold:
            own["Action"] = ""
        else:
            animation = "Use"
        
    animation = PLAYER_ANIMS[animation]
    armature.playAction("Player", animation[0], animation[1], blendin=2)


def processMovement(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    axis = own.childrenRecursive["CameraAxis"] # type: KX_GameObject
    
    moveVec = Vector([0.0, 0.0, 0.0])
    axis.worldPosition = own.worldPosition
    axis.worldPosition.y -= PLAYER_CAMERA_DISTANCE
    
    if own["Moving"] and not own["Action"]:
        moveVec.x = PLAYER_MOV_SPEED
        
    if own["Direction"] == "L":
        moveVec.x *= -1
        axis.worldPosition.x -= PLAYER_CAMERA_FORWARD
        
    else:
        axis.worldPosition.x += PLAYER_CAMERA_FORWARD
        
    own.applyMovement(moveVec)