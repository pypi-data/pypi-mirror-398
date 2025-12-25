import logging
import secrets
import time

import ipywidgets as widgets
from esrf_pathlib import ESRFPath as Path

logger = logging.getLogger(__name__)


class Status:
    def __init__(self):
        self.details = []
        self.problem_list = []
        self.detailedOK = False
        self.statusDetailedLaunched = False
        self.filesOk = False
        self.statusFilesLaunched = False
        self.testPassMsg = [
            "✅ Success! This step didn’t even break a sweat. 🎉",
            "✅ Step complete! The code gods are smiling upon you. 🙏",
            "✅ Nailed it! That was smoother than a penguin on ice. 🐧",
            "✅ Success! You’ve got this down to a science... or maybe an art. 🎨",
            "✅ Boom! You’re making it look easy. Ever thought about going pro? 🏆",
            "✅ Flawless! Even the bugs are giving you a standing ovation. 🐛👏",
            "✅ Great job! At this rate, you’ll finish before your coffee gets cold. ☕",
            "✅ You did it! This step didn’t stand a chance. 💥",
            "✅ Perfect! If coding had a red carpet, you’d be walking it. 🎬",
            "✅ Mission accomplished! Go ahead, give yourself a high-five. 👏",
            "✅ Impressive! This code is practically writing itself. 🖋️✨",
            "✅ Victory! You’re leveling up like a pro gamer. 🎮🚀",
            "✅ Bravo! This step ran smoother than a buttered slide. 🧈",
            "✅ Success! The code approves of your dedication. 👩‍💻💖",
            "✅ Hooray! You’re cruising through this project. 🛥️💨",
            "✅ Step complete! Even your computer’s impressed. 🖥️😎",
            "✅ High five! Another step down, many more to conquer! ✋",
            "✅ Yesss! You crushed it. Keep going! 🥊",
            "✅ Nicely done! This code didn’t see you coming. 🕶️",
            "✅ Huzzah! You’re coding like a wizard. 🧙‍♂️✨",
            "✅ Well done! You made it look too easy. 😄",
            "✅ Mission accomplished! No bugs detected. 💯",
            "✅ Success! You’re making coding look like child’s play. 🧩",
            "✅ Woohoo! Another win in the bag. 🎒",
            "✅ Fantastic! This code has met its match. 😎",
            "✅ That’s it! You could teach a masterclass in this. 👨‍🏫",
            "✅ Amazing! You’re one step closer to coding greatness. 🏅",
            "✅ Yay! You’re blazing through this like a rocket. 🚀",
            "✅ You’ve done it! Even the keyboard’s cheering for you. ⌨️🎉",
            "✅ Wow! This step didn’t stand a chance. 💥",
            "✅ Complete! That’s how it’s done! 🏆",
            "✅ Nice one! It’s almost too easy for you. 🎩✨",
            "✅ Cheers! You’re cruising through the code. 🍹",
            "✅ Excellent work! You’re like the code whisperer. 🧙‍♀️",
            "✅ Crushed it! Success tastes pretty sweet, huh? 🍬",
            "✅ Victory! Code is afraid of you now. 😂",
            "✅ Perfecto! You could do this in your sleep. 😴",
            "✅ Legendary! You’re making history, one step at a time. 📜",
            "✅ Not a glitch in sight—just pure talent! 👌",
            "✅ Nailed it! The code’s totally under your spell. 🪄",
            "✅ Gold star for you! 🌟 Keep ‘em coming!",
            "✅ A+ work! The code is in awe. 🏅",
            "✅ Done and dusted! Is there anything you can’t do? 😆",
            "✅ Smooth as silk! You’re unstoppable. 🧵",
            "✅ Boom! This step got owned. 💥",
            "✅ Finished! The code trembles before you. 😎",
            "✅ You’re a star! Nothing can stop you now. 🌟",
            "✅ Epic! You’re breezing through. 🍃",
            "✅ Just like that! You’re a step-finishing machine. 🤖",
            "✅ Brilliant! The code didn’t know what hit it. 💡",
            "✅ Outstanding! You’re coding circles around everyone. 🔄",
            "✅ Incredible! You make this look like a walk in the park. 🌳",
            "✅ Fantastic! Code can’t keep up with you. 💫",
            "✅ On point! You nailed that like a pro. 🔨",
            "✅ Hats off to you! 🎩 Another flawless step!",
            "✅ Wonderful! You and the code are best buds now. 🤝",
            "✅ Score! Another victory for the team! 🥳",
            "✅ Success! Your keyboard probably needs a break. 🖱️",
            "✅ Perfecto! Code is officially tamed. 🦁",
            "✅ Complete! You could do this all day. 💪",
            "✅ Spectacular! Your skills are unreal. 🤩",
            "✅ Oh yeah! You’re taking charge. ⚡",
            "✅ This is mastery! Keep going, maestro. 🎼",
            "✅ Victory dance time! 💃 You earned it!",
            "✅ Bravo! The code world salutes you. 🫡",
            "✅ Hey now! You’re a coding rockstar. 🎸",
            "✅ Nice job! Your code has a new hero. 🦸‍♂️",
            "✅ Killer job! You’re making this look like magic. 🪄",
            "✅ One more down! You’ve got the Midas touch. ✨",
            "✅ Done! You’re on a roll, keep going! 🎡",
            "✅ Gold medal performance! 🥇 Keep shining!",
            "✅ You crushed it—again! Total rockstar. 🌟",
            "✅ Magic! This step just vanished in your hands. 🧙‍♂️",
            "✅ Victory achieved! You’re on fire! 🔥",
            "✅ Pat on the back! You’re acing this. 👏",
            "✅ Legend status unlocked! 🏆 Keep it up!",
            "✅ You just made that look like a breeze. 🍃",
            "✅ You did it! The code waves the white flag. 🚩",
            "✅ Whoa! The code knows who’s boss. 👑",
            "✅ Spot on! This step didn’t stand a chance. 🎯",
            "✅ Nailed it! At this rate, you’ll break records. 🥇",
            "✅ Crushed! Code is no match for you. 💪",
            "✅ Great work! That step practically coded itself. 🤖",
            "✅ Brilliance confirmed. Next step, please! 🧠",
            "✅ High score! You’re racking up wins. 🏆",
            "✅ Boom! You own this code. 🏢",
            "✅ Wonderful! The code never saw it coming. 😆",
            "✅ Just wow. You’re the hero of this code. 🦸‍♀️",
            "✅ Perfect! This step was just a warm-up. 🎬",
            "✅ You did it! The code can rest now. 🛏️",
            "✅ Congrats! This project’s in the bag. 🎒",
            "✅ Straight A’s in code completion! 🅰️",
            "✅ Ten out of ten! Master level stuff here. 🔥",
            "✅ Fantastic work! Code is officially humbled. 😂",
            "✅ Oh yeah! Victory never looked so good. 😎",
            "✅ Solid win! Code’s got nothing on you. 🏆",
            "✅ Champion! You’re conquering this project. 🏅",
            "✅ Full marks! The code didn’t stand a chance. 💯",
            "✅ Done! You’re coding like a legend. ⚔️",
            "✅ That’s it! You’re officially unstoppable. 🌌",
        ]
        self.testFailMsg = [
            "❌ Well, that went as smoothly as a knight on roller skates. 🤦‍♂️ You'd better contact the dev team !",
            "❌ Congratulations! You’ve just achieved the impossible... a complete flop! 🎉 You'd better contact the dev team !",
            "❌ Oops! You’ve made a mess bigger than Arthur's last strategy meeting. 🏰 You'd better contact the dev team !",
            "❌ Looks like you’ve got more errors than the Round Table has knights! ⚔️ You'd better contact the dev team !",
            "❌ Oh là là! That was a swing and a miss—like Perceval trying to catch a fish! 🎣 You'd better contact the dev team !",
            "❌ Yikes! That went about as well as a wedding at Kaamelott. 💔 You'd better contact the dev team !",
            "❌ Oops! You’ve entered the realm of epic fail, right next to Lancelot’s love life. 😅 You'd better contact the dev team !",
            "❌ Well, that didn’t quite hit the mark... like Arthur’s attempts at swordplay! ⚔️ You'd better contact the dev team !",
            "❌ Congratulations! You’ve unlocked the ‘How Not to Code’ achievement. 🏆 You'd better contact the dev team !",
            "❌ That’s a classic! Even Merlin couldn’t have predicted this mess. 🧙‍♂️ You'd better contact the dev team !",
            "❌ Looks like you just stumbled into a plot twist even the writers didn’t see coming! 📜 You'd better contact the dev team !",
            "❌ Failed spectacularly—like a catapult built by the Knights of the Round Table! 🏹 You'd better contact the dev team !",
            "❌ Well, that escalated quickly... faster than Arthur’s patience. ⏳ You'd better contact the dev team !",
            "❌ That was a noble effort! Too bad it was more of a tragedy than a comedy. 🎭 You'd better contact the dev team !",
            "❌ Ah, the sweet taste of failure! Like drinking mead at an empty table. 🍻 You'd better contact the dev team !",
            "❌ Oops! You’ve just outdone Galahad at miscalculating a quest. 📉 You'd better contact the dev team !",
            "❌ That didn’t go as planned—like a banquet without food! 🍗 You'd better contact the dev team !",
            "❌ Well, that’s a wrap! And not the good kind, like the one at the end of a feast. 🎬 You'd better contact the dev team !",
            "❌ Congratulations! You’ve just set a new record for ‘most epic fails’ in Kaamelott. 🥇 You'd better contact the dev team !",
            "❌ Failure achieved! You’ve outdone even the worst decisions of the Round Table. 🙈 You'd better contact the dev team !",
            "❌ That went about as well as a diplomatic mission led by Yvain. 🤦‍♂️ You'd better contact the dev team !",
            "❌ You’ve made a mess bigger than the kitchen after a feast! 🍽️ You'd better contact the dev team !",
            "❌ Wow! That was a disaster! Even the knights are shaking their heads. 🤷‍♂️ You'd better contact the dev team !",
            "❌ Oh, dear! You’ve just entered the Hall of Fails—welcome! 🚪 You'd better contact the dev team !",
            "❌ Well, that was a failure worthy of a bard's ballad! 🎶 You'd better contact the dev team !",
            "❌ Looks like you’ve pulled a classic Perceval! 🤦‍♂️ You'd better contact the dev team !",
            "❌ That was an ‘Arthur’s strategy’ level fail! 🏰 You'd better contact the dev team !",
            "❌ Oops! You’ve just created a new version of ‘How Not to Do It.’ 📚 You'd better contact the dev team !",
            "❌ Congratulations! You’re now the proud owner of a spectacular fail! 🏆 You'd better contact the dev team !",
            "❌ That went south faster than a knight running from a dragon! 🐉 You'd better contact the dev team !",
            "❌ Well, that’s one way to make a bad situation worse! 👑 You'd better contact the dev team !",
            "❌ Oops! You’ve tripped over your own ambitions, like Lancelot on a horse! 🐎 You'd better contact the dev team !",
            "❌ Failure alert! This is going in the ‘Things Not to Do’ manual. 📜 You'd better contact the dev team !",
            "❌ Well, that was a misadventure! Like a quest without a map! 🗺️ You'd better contact the dev team !",
            "❌ Oops! You’ve taken the scenic route to failure. 🌄 You'd better contact the dev team !",
            "❌ That went as well as a jousting match with a blindfold. 🤷‍♂️ You'd better contact the dev team !",
            "❌ Congratulations! You’ve just achieved ‘total chaos’ status! 🎉 You'd better contact the dev team !",
            "❌ Yikes! That was worse than a banquet without wine! 🍷 You'd better contact the dev team !",
            "❌ Looks like you’ve stumbled into the ‘Fails’ section of Kaamelott’s library! 📚 You'd better contact the dev team !",
            "❌ Well, that was about as successful as a battle against a dragon armed with a spoon! 🥄 You'd better contact the dev team !",
            "❌ Oops! You’ve just opened the floodgates of fail! 🌊 You'd better contact the dev team !",
            "❌ That was an adventure worthy of a fool’s cap! 🎩 You'd better contact the dev team !",
            "❌ Congratulations! You’re now a member of the ‘What Not to Do’ club! 🥳 You'd better contact the dev team !",
            "❌ That went south faster than Arthur’s confidence in his knights! ⚔️ You'd better contact the dev team !",
            "❌ Wow! You’ve just crafted a masterpiece of failure! 🎨 You'd better contact the dev team !",
            "❌ Well, that didn’t go as planned... like a quest with no treasure! 💰 You'd better contact the dev team !",
            "❌ Oops! You’ve just added a new chapter to the ‘Epic Fails of Kaamelott’ saga! 📖 You'd better contact the dev team !",
            "❌ Failure! Like trying to find a dragon in a haystack! 🐉 You'd better contact the dev team !",
            "❌ Yikes! That’s going to leave a mark—like an angry dragon’s claw! 🐉 You'd better contact the dev team !",
            "❌ That was more of a flop than a fish out of water! 🐟 You'd better contact the dev team !",
            "❌ Congratulations! You’ve achieved failure at a grand scale! 🎪 You'd better contact the dev team !",
            "❌ Oops! That went about as well as Gauvain’s attempts to flirt! 💔 You'd better contact the dev team !",
            "❌ Well, that was a swing and a miss—like Arthur’s last battle plan! ⚔️ You'd better contact the dev team !",
            "❌ Looks like you’ve just entered the ‘Hall of Regrets!’ 🚪 You'd better contact the dev team !",
            "❌ Congratulations! You’ve created a new definition of failure! 📖 You'd better contact the dev team !",
            "❌ Oops! That was as smooth as a rough-hewn sword! ⚔️ You'd better contact the dev team !",
            "❌ Well, that didn’t go well—like a knight without armor! 🛡️ You'd better contact the dev team !",
            "❌ Wow! You’ve unlocked the ‘Epic Fail’ achievement! 🏅 You'd better contact the dev team !",
            "❌ Yikes! That was a flop worthy of a bard’s lament! 🎭 You'd better contact the dev team !",
            "❌ That went as well as a banquet without any knights! 🍽️ You'd better contact the dev team !",
            "❌ Oops! You’ve taken the scenic route to failure! 🏞️ You'd better contact the dev team !",
            "❌ Well, that’s a classic! Even Merlin would raise an eyebrow. 🤔 You'd better contact the dev team !",
            "❌ Congratulations! You’ve turned a minor issue into a major catastrophe! 🚨 You'd better contact the dev team !",
            "❌ That was as successful as a quest for a dragon without a sword! 🗡️ You'd better contact the dev team !",
            "❌ Oops! You’ve created a masterpiece of mishaps! 🎨 You'd better contact the dev team !",
            "❌ Well, that was a miscalculation of epic proportions! 📊 You'd better contact the dev team !",
            "❌ That went south faster than a knight in a dragon’s lair! 🏰 You'd better contact the dev team !",
            "❌ Yikes! You’ve tripped over your own ambitions! 👣 You'd better contact the dev team !",
            "❌ Congratulations! You’ve just set a new record for fails! 📊 You'd better contact the dev team !",
            "❌ Oops! That went about as smoothly as a sword fight with a pillow! 🛏️ You'd better contact the dev team !",
            "❌ Wow! You’ve just crafted a new definition of chaos! 🎉 You'd better contact the dev team !",
            "❌ That went as well as a wedding in a dragon’s den! 💍 You'd better contact the dev team !",
            "❌ Oops! You’ve just stumbled into failure like Perceval into a pond! 🌊 You'd better contact the dev team !",
            "❌ Well, that’s one way to make a mess of things! 🍽️ You'd better contact the dev team !",
            "❌ Congratulations! You’ve just written a new chapter in the Book of Fails! 📖 You'd better contact the dev team !",
            "❌ Yikes! That was a disaster of epic proportions! 🌪️ You'd better contact the dev team !",
            "❌ That went south faster than Lancelot's love life! ❤️ You'd better contact the dev team !",
            "❌ Oops! You’ve just entered the realm of epic fail! 🚪 You'd better contact the dev team !",
            "❌ Well, that was a flop—like trying to train a dragon! 🐉 You'd better contact the dev team !",
            "❌ Congratulations! You’ve just achieved the ultimate fail! 🎉 You'd better contact the dev team !",
            "❌ Yikes! That’s going to be a hard one to explain! 🤦‍♂️ You'd better contact the dev team !",
            "❌ Oops! You’ve created a classic example of what not to do! ❌ You'd better contact the dev team !",
            "❌ Well, that was about as successful as a feast without food! 🍗 You'd better contact the dev team !",
            "❌ Congratulations! You’re now a proud member of the Epic Fails Club! 🥳 You'd better contact the dev team !",
            "❌ That went about as well as a jousting match in a windstorm! 🌪️ You'd better contact the dev team !",
            "❌ Oops! You’ve just crafted a masterpiece of disaster! 🎨 You'd better contact the dev team !",
            "❌ Well, that was a swing and a miss—like Arthur’s last attempt at diplomacy! 🏰 You'd better contact the dev team !",
            "❌ Congratulations! You’ve made failure an art form! 🎨 You'd better contact the dev team !",
            "❌ That went south faster than a knight running from a dragon! 🐉 You'd better contact the dev team !",
            "❌ Oops! You’ve just tripped over your own expectations! 👣 You'd better contact the dev team !",
            "❌ Well, that was a classic! Even the knights are chuckling. 🤭 You'd better contact the dev team !",
            "❌ Congratulations! You’ve just crafted a new chapter in the Book of Fails! 📖 You'd better contact the dev team !",
            "❌ Yikes! That was a misadventure worthy of a bard’s tale! 🎶 You'd better contact the dev team !",
            "❌ Oops! That’s one way to create chaos! 🎉 You'd better contact the dev team !",
            "❌ Well, that didn’t go as planned—like a banquet without wine! 🍷 You'd better contact the dev team !",
            "❌ Congratulations! You’ve achieved the impossible... a total disaster! 🎉 You'd better contact the dev team !",
            "❌ That went about as well as a dragon’s tea party! 🍵 You'd better contact the dev team !",
        ]

    def print_errors(self, disp=False):
        if self.problem_list:
            if disp:
                print(self.problem_list)
            return f"{self.__class__.__name__}: {'<br> - '.join(self.problem_list)}"
        else:
            return "No error to display."

    def print_status(self, disp=False):
        if not self.statusFilesLaunched:
            self.loadStatusFiles()
        out = []
        if self.filesOk:
            if self.details:
                _str = "<br> - ".join(self.details)
            else:
                _str = "<br> - " + secrets.choice(self.testPassMsg)
        elif self.problem_list:
            _str = "<br> - ❌ ".join(self.problem_list)
        else:
            _str = "<br> - " + secrets.choice(self.testFailMsg)
        out.append(f"{self.__class__.__name__}: {_str}")
        if disp:
            print(out)
        return out

    def print_status_details(self, disp=False):
        if not self.statusDetailedLaunched:
            self.loadStatusDetailed()
        out = []
        if self.detailedOK:
            if self.details:
                _str = "<br> - ".join(self.details)
            else:
                _str = "<br> - " + secrets.choice(self.testPassMsg)
        elif self.problem_list:
            _str = "<br> - ❌ ".join(self.problem_list)
        else:
            _str = "<br> - " + secrets.choice(self.testFailMsg)
        out.append(f"{self.__class__.__name__}: {_str}")
        if disp:
            print(out)
        return out

    def loadStatusFiles(self, *args):
        self.statusFilesLaunched = True
        self.problem_list = []
        self.details = []

    def loadStatusDetailed(self, *args):
        self.statusDetailedLaunched = True
        if not self.statusFilesLaunched:
            self.loadStatusFiles(*args)
        self.detailedOK = self.filesOk


class Experiment:
    def __init__(self):
        self.parameters = Status()
        self.components = [(self.parameters, [], "Parameters")]
        self.statusDetailedLaunched = False
        self.statusFilesLaunched = False
        self.post_treatment = [widgets.Label("No components available")]

    @property
    def detailedOK(self):
        temp = [
            comp.detailedOK
            for comp, _, _ in self.components
            if hasattr(comp, "detailedOK")
        ]
        if temp:
            return all(temp)
        else:
            return False

    @property
    def filesOk(self):
        temp = [
            comp.filesOk for comp, _, _ in self.components if hasattr(comp, "filesOk")
        ]
        if temp:
            return all(temp)
        else:
            return False

    def __repr__(self):
        return f"{self.name}"

    def loadStatusDetailed(self):
        self.statusDetailedLaunched = True
        for component, args, _ in self.components:
            component.loadStatusDetailed(*args)

    def print_status_details(self, disp=False):
        if not self.statusDetailedLaunched:
            self.loadStatusDetailed()
        out = []
        for component, _, _ in self.components:
            out.append(component.print_status_details())
        if disp:
            print(out)
        return out

    def loadStatusFiles(self):
        self.statusFilesLaunched = True
        dataset_label = self._log_identifier()
        for component, args, label in self.components:
            start = time.perf_counter()
            success = False
            try:
                component.loadStatusFiles(*args)
                success = True
            except Exception:  # noqa: BLE001
                elapsed = time.perf_counter() - start
                logger.exception(
                    "%s: loadStatusFiles for component %s (%s) failed after %.2fs",
                    dataset_label,
                    component.__class__.__name__,
                    label,
                    elapsed,
                )
                raise
            finally:
                if logger.isEnabledFor(logging.DEBUG):
                    elapsed = time.perf_counter() - start
                    logger.debug(
                        "%s: loadStatusFiles for component %s (%s) %s in %.2fs",
                        dataset_label,
                        component.__class__.__name__,
                        label,
                        "completed" if success else "failed",
                        elapsed,
                    )

    def print_status(self, disp=False):
        if not self.statusFilesLaunched:
            self.loadStatusFiles()
        out = []
        for component, _, _ in self.components:
            out.extend(component.print_status())
        if disp:
            print(out)
        return out

    def print_errors(self, disp=False):
        if not self.statusFilesLaunched:
            self.loadStatusFiles()
        out = []
        for component, _, _ in self.components:
            out.extend(component.print_errors())
        if disp:
            print(out)
        return out

    def _log_identifier(self) -> str:
        if hasattr(self, "main_path"):
            return str(self.main_path)
        return getattr(self, "name", self.__class__.__name__)


class CheckFile(Status):
    def __init__(self, dpath: Path, dtype: Path, visualize=False):
        super().__init__()
        self.main_path = Path(dpath)
        self.type = Path(dtype)
        self.target_files = None
        self.ext = self.type.suffix or None
        self.file = self.type.stem
        self.visualize = visualize

    @staticmethod
    def check_files_glob(
        directory: str, keyword: str, extensions: list[str] = (".h5", ".hdf5")
    ):
        matching_files = []
        directory_path = Path(directory)

        # Loop through each extension pattern
        for ext in extensions:
            pattern = f"*{keyword}*{ext}"
            matching_files.extend(
                directory_path.rglob(pattern)
            )  # Use Path.glob for consistency

        return matching_files

    def loadStatusFiles(self):
        super().loadStatusFiles()
        self.statusFilesLaunched = True
        self.target_files = self.check_files_glob(
            str(self.main_path),
            self.file,
            (
                [
                    self.ext,
                ]
                if self.ext
                else [".h5", ".hdf5"]
            ),
        )
        self.filesOk = bool(self.target_files)
