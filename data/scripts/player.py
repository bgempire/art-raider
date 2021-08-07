import bge

from bge.types import *
from bge.logic import KX_ACTION_MODE_PLAY as PLAY, KX_ACTION_MODE_LOOP as LOOP
from mathutils import Vector
from .bgf import state


DEBUG = 0
PLAYER_COLLISION_DOOR_DISTANCE = 0.5
PLAYER_COLLISION_ITEM_DISTANCE = 1.0
PLAYER_MOV_SPEED = 0.05
PLAYER_CAMERA_SLOW_PARENT = 60.0
PLAYER_CAMERA_FORWARD = 1
PLAYER_CAMERA_DISTANCE = 5
PLAYER_DEFAULT_PROPS = {
    "Dead" : False,
    "Direction" : "R",
    "Moving" : False,
    "Action" : "",
}
PLAYER_ANIMS = {
    "Idle" : (0, 59, LOOP),
    "Walk" : (70, 89, LOOP),
    "Use" : (100, 115, PLAY),
    "Death" : (120, 145, PLAY),
    "StairsUpRight" : (150, 177, PLAY),
    "StairsDownRight" : (180, 207, PLAY),
    "StairsUpLeft" : (210, 237, PLAY),
    "StairsDownLeft" : (240, 267, PLAY),
    "StairsEvenRight" : (270, 297, PLAY),
    "StairsEvenLeft" : (300, 327, PLAY),
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
    
    if not _collision in own.collisionCallbacks:
        own.collisionCallbacks.append(_collision)
    
    if not "Player" in own.scene:
        own.scene["Player"] = own
    
    for prop in PLAYER_DEFAULT_PROPS.keys():
        own[prop] = PLAYER_DEFAULT_PROPS[prop]
        if DEBUG: own.addDebugProperty(prop)
        
    _initScenery(cont)


def setProps(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    door = own.scene["DoorCollided"] # type: KX_GameObject
    item = own.scene["ItemCollided"] # type: KX_GameObject
    
    keyUp = bge.logic.keyboard.events[bge.events.WKEY] == 1
    keyLeft = bge.logic.keyboard.events[bge.events.AKEY] == 2
    keyRight = bge.logic.keyboard.events[bge.events.DKEY] == 2
    
    if not own["Dead"] and not own["Action"].startswith("Door"):
        
        if keyUp and not own["Action"]:
            if door and door["Valid"] and own.getDistanceTo(door) < PLAYER_COLLISION_DOOR_DISTANCE:
                own.worldPosition = door.worldPosition
                own["Action"] = "DoorIn"
                own["Direction"] = "L" if door["DirectionH"] == "Left" else "R"
            else:
                own["Action"] = "Use"
                
                if item and item["Valid"] and own.getDistanceTo(item) < PLAYER_COLLISION_ITEM_DISTANCE:
                    item["Valid"] = False
                    state["ItemsCollected"] += 1
                    
                    for obj in item.groupObject.groupMembers:
                        if "ITEM_MESH" in obj:
                            obj.visible = False
                            own.scene.addObject("ItemPlus1", obj, 60)
                            break
        
        elif not own["Action"] and keyLeft and not keyRight:
            own["Direction"] = "L"
            own["Moving"] = True
            
        elif not own["Action"] and not keyLeft and keyRight:
            own["Direction"] = "R"
            own["Moving"] = True
            
        elif not keyLeft and not keyRight or keyLeft and keyRight or own["Action"]:
            own["Moving"] = False
            
    elif own["Action"] == "Door":
        print("Door transition")
            
    if own["Dead"] and not "DeathPlayed" in own:
        own["Action"] = "Death"
        

def processAnimation(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    armature = own.childrenRecursive["PlayerArmature"] # type: BL_ArmatureObject
    door = own.scene["DoorCollided"] # type: KX_GameObject
    
    animation = "Idle"
    actionFrame = int(armature.getActionFrame())
    
    if not own["Dead"]:
            
        # Invert armature direction
        if own["Direction"] == "L":
            armature.localScale.x = -1
        else:
            armature.localScale.x = 1
        
        if not own["Action"]:
            
            if own["Moving"]:
                animation = "Walk"
                
        elif own["Action"] == "Use":
            frameThreshold = int(PLAYER_ANIMS["Use"][1])
            
            if actionFrame >= frameThreshold-2 and actionFrame <= frameThreshold:
                own["Action"] = ""
                
                if state["ItemsTotal"] > 0 and state["ItemsCollected"] == state["ItemsTotal"]:
                    own["Action"] = "Cleared"
                    win = own.scene.addObject("PlayerWin", own, 60) # type: KX_GameObject
                    win.worldPosition.z += 0.8
            else:
                animation = "Use"
                
        elif own["Action"] == "DoorIn":
            own.suspendDynamics(True)
            anim = PLAYER_ANIMS["Stairs" + door["DirectionV"] + door["DirectionH"]]
            frameThreshold = int(anim[1])
            armature.playAction("Player", anim[0], anim[1], layer=1)
            
            if armature.getActionFrame(1) >= frameThreshold-2 and armature.getActionFrame(1) <= frameThreshold:
                armature.stopAction(1)
                own.worldPosition = door["Target"].worldPosition
                own["Action"] = "DoorOut"
                own.scene["DoorCollided"] = door = door["Target"]
                
            animation = "Walk"
                
        elif own["Action"] == "DoorOut":
            own["Direction"] = "R" if door["DirectionH"] == "Left" else "L"
            anim = PLAYER_ANIMS["Stairs" + door["DirectionV"] + door["DirectionH"]]
            frameThreshold = int(anim[0])
            armature.playAction("Player", anim[1], anim[0], layer=1)
            
            if armature.getActionFrame(1) >= frameThreshold and armature.getActionFrame(1) <= frameThreshold+2:
                own["Action"] = ""
                armature.stopAction(1)
                own.restoreDynamics()
                
            animation = "Walk"
                
    else:
        animation = "Death" if not "DeathPlayed" in own else ""
        
        frameThreshold = int(PLAYER_ANIMS["Death"][1])
        
        if actionFrame >= frameThreshold-2 and actionFrame <= frameThreshold:
            own["Action"] = ""
            own["DeathPlayed"] = True
            for obj in own.childrenRecursive:
                if "DeathStars" in obj.name:
                    obj.visible = True
                    
    if animation in PLAYER_ANIMS.keys() and (not own["Dead"] or own["Action"]):
        animation = PLAYER_ANIMS[animation]
        armature.playAction(
            "Player", animation[0], animation[1], 
            blendin=2, play_mode=animation[2]
        )


def processMovement(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    axis = own.childrenRecursive["CameraAxis"] # type: KX_GameObject
    
    moveVec = Vector([0.0, 0.0, 0.0])
    axis.worldPosition = own.worldPosition
    axis.worldPosition.y -= PLAYER_CAMERA_DISTANCE
    
    if not own["Dead"] and own["Moving"] and not own["Action"]:
        moveVec.x = PLAYER_MOV_SPEED
        own.worldPosition.y = 0
        
    if own["Direction"] == "L":
        moveVec.x *= -1
        axis.worldPosition.x -= PLAYER_CAMERA_FORWARD
        
    else:
        axis.worldPosition.x += PLAYER_CAMERA_FORWARD
        
    own.applyMovement(moveVec)


def _initScenery(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    scene = own.scene
    scene["Doors"] = doors = scene["Doors"] if "Doors" in scene else {}
    scene["Items"] = items = scene["Items"] if "Items" in scene else {}
    scene["DoorCollided"] = scene["DoorCollided"] if "DoorCollided" in scene else None
    scene["ItemCollided"] = scene["ItemCollided"] if "ItemCollided" in scene else None
    
    for obj in own.scene.objects:
        obj = obj # type: KX_GameObject
        
        if "DOOR" in obj:
            obj["Valid"] = False
            
            if obj.groupObject and "Door" in obj.groupObject:
                if not obj.groupObject["Door"] in doors.keys():
                    doors[obj.groupObject["Door"]] = [obj]
                else:
                    doors[obj.groupObject["Door"]].append(obj)
                    
        elif "ITEM" in obj:
            obj["Valid"] = False
            
            if obj.groupObject and "Item" in obj.groupObject and obj.groupObject["Item"] in range(1, 6):
                
                for member in obj.groupObject.groupMembers:
                    member = member # type: KX_GameObject
                    
                    if "ITEM_MESH" in member:
                        state["ItemsTotal"] += 1
                        obj["Valid"] = True
                        member.replaceMesh("Item" + str(obj.groupObject["Item"]))
                        member.visible = True
                        break
                
    doorsKeys = tuple(doors.keys())
    for door in doorsKeys:
        if len(doors[door]) != 2:
            del doors[door]
            
        else:
            curDoors = doors[door] # type: list[KX_GameObject]
            
            curDoors[0]["Target"] = curDoors[1]
            curDoors[0]["Valid"] = True
            curDoors[1]["Target"] = curDoors[0]
            curDoors[1]["Valid"] = True
            
            if int(curDoors[0].worldPosition.z) > int(curDoors[1].worldPosition.z):
                curDoors[0]["DirectionV"] = "Down"
                curDoors[1]["DirectionV"] = "Up"
            elif int(curDoors[0].worldPosition.z) < int(curDoors[1].worldPosition.z):
                curDoors[0]["DirectionV"] = "Up"
                curDoors[1]["DirectionV"] = "Down"
            else:
                curDoors[0]["DirectionV"] = "Even"
                curDoors[1]["DirectionV"] = "Even"
                
            if int(curDoors[0].worldPosition.x) < int(curDoors[1].worldPosition.x):
                curDoors[0]["DirectionH"] = "Right"
                curDoors[1]["DirectionH"] = "Left"
            elif int(curDoors[0].worldPosition.x) > int(curDoors[1].worldPosition.x):
                curDoors[0]["DirectionH"] = "Left"
                curDoors[1]["DirectionH"] = "Right"
            else:
                curDoors[0]["DirectionH"] = "Left"
                curDoors[1]["DirectionH"] = "Left"


def _collision(obj, point, normal):
    # type: (KX_GameObject, Vector, Vector) -> None
    
    player = obj.scene["Player"] # type: KX_GameObject
    
    if "DOOR" in obj and obj["Valid"]:
        obj.scene["DoorCollided"] = obj
    
    elif "ITEM" in obj and obj["Valid"]:
        obj.scene["ItemCollided"] = obj
    
    elif "DAMAGE" in obj and obj["Damage"] and not player["Dead"]:
        player["Dead"] = True
        powObj = obj.scene.addObject("GuardPow") # type: KX_GameObject
        powObj.worldPosition = point
        powObj.worldPosition.y -= 0.5