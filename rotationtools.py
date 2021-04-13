#!/usr/bin/env python3
import matplotlib.pyplot as plt
import damage
import abilities

def shorthand(s):
    autos = s.count('a')
    steadies = s.count('s')
    multis = s.count('m')
    arcanes = s.count('A')
    weaves = s.count('w')
    raptors = s.count('r')
    out = str(steadies) + ':' + str(autos)
    if (multis>0) or (arcanes>0):
        out = out + ':' + str(multis) + ':' + str(arcanes)
    if (weaves>0) or (raptors>0):
        out = out + ' ' + str(weaves+raptors) + 'w'
    return out


class rotationplot:
    ranged = damage.AverageRangedDamage(
        damage.Weapon(83.3, 3.0),
        damage.Ammo(32),
        2696, 39.12, 1.2 * 1.15,
        1.02 * 1.04 * (1 + 0.8 * 0.03)**3
    )

    melee = damage.AverageMeleeDamage(
        damage.Weapon(118.6, 3.7),
        2300, 34.12, 1,
        1.02 * 1.04 * (1 + 0.8 * 0.03)**3
    )

    rotation_string = ''

    current_time = 0
    total_damage = 0
    remaining_armor = 6200 - 3075 - 610 - 800 # base - iEA - FF - CoR

    abilities = abilities.create(ranged, melee)
    hawk_until = 0

    ax = ()
    showlabels = 1 # set to true to show labels on all shotss
    rot_stats = 'Ranged speed: {speed:.1f}\nRanged haste: {haste:.2f}\nDuration: {dur:.2f}'
    dps_stats = 'rAP: {rap:.0f}\nmAP: {map:.0f}\nCrit: {crit:.1f}%\nDPS: {dps:.0f}'
    row0 = {
        'Auto': 0.1,
        'Cast': 1.1,
        'GCD': 2.1,
    }

    def init_fig(self):
        self.clear()
        fig, self.ax = plt.subplots(figsize=(20,8), dpi=100)

    def clear(self):
        self.rotation_string = ''
        self.current_time = 0
        self.total_damage = 0

        for ability in self.abilities.values():
            ability.reset()

        self.ax = 0


    def recalc(self):
        s = self.rotation_string
        self.clear()
        self.add_rotation(s)

    def calc_dur(self):
        return max([
            self.abilities[ability].available - self.abilities[ability].first_usage
            for ability in abilities.ABILITIES_WITH_CD
        ])

    def calc_dps(self):
        #end_time = max(self.auto_available, self.multi_available, self.arcane_available, self.melee_available, self.raptor_available)
        end_time = self.calc_dur()
        self.dps = self.total_damage / end_time * (1 - (self.remaining_armor / ((467.5 * 70) + self.remaining_armor - 22167.5)))
        return self.dps

    def complete_fig(self):
        self.ax.set_xlim(-0.25, 14)
        self.ax.set_ylim(0, 3)
        self.ax.set_yticks([0.5, 1.5, 2.5])
        self.ax.set_yticklabels(self.row0.keys())
        self.ax.set_xlabel('time [s]')
        labels = list(self.abilities.keys())
        handles = [plt.Rectangle((0,0),1,1, color=self.abilities[label].color) for label in labels]
        plt.legend(handles, labels, bbox_to_anchor=(1.01, 1), loc='upper left')
        self.calc_dps()
        rota = self.rot_stats.format(speed = self.ranged.speed(), haste = self.ranged.haste, dur=self.abilities['auto'].available)
        plt.annotate(rota,(0.85,0.5), xycoords='axes fraction')
        stats = self.dps_stats.format(rap=self.ranged.ap,map=self.melee.ap,crit=self.ranged.crit,dps=self.dps)
        plt.annotate(stats,(0.85,0.3), xycoords='axes fraction')
        plt.annotate(
            abilities.create_breakdown(self.abilities, self.total_damage),
            (1.01, -0.02), xycoords='axes fraction'
        )
        #plt.annotate('Range haste: '+str(self.haste),(1.01,0.455), xycoords='axes fraction')
        plt.show()

    def add_ability(self, ability_name, y1, update_time = True):
        ability = self.abilities[ability_name]

        if ability.available > self.current_time:
            self.current_time = ability.available

        self.add_concrete_ability(ability, y1, None, update_time)

    def add_concrete_ability(self, ability, y1, x0 = None, update_time = True):
        if (x0 is None):
            x0 = self.current_time

        if self.ax:
            self.ax.bar(
                x0, ability.height, ability.duration, y1,
                facecolor = 'white',
                edgecolor = ability.color,
                align = 'edge'
            )

        if self.ax and self.showlabels and ability.has_annotation:
            plt.annotate(
                ability.annotation, (ability.duration / 2, y1 + 0.4),
                ha='center', va='center'
            )

        self.total_damage = self.total_damage + ability.damage

        if (update_time):
            ability.use(self.current_time)
            self.current_time = self.current_time + ability.duration

    def add_auto(self):
        auto = self.abilities['auto']

        if (auto.available < self.current_time):
            self.add_concrete_ability(
                abilities.auto_delay(self.current_time - auto.available),
                0.4, auto.available, False
            )

        self.add_ability('auto', self.row0['Auto'])

    def add_gcd_ability(self, ability_name):
        self.add_ability('gcd', self.row0['GCD'], False)
        self.add_ability(ability_name, self.row0['Cast'])

    def add_raptor(self):
        print(self.current_time)
        self.add_ability('raptor', self.row0['Cast'])

    def add_melee(self):
        print(self.current_time)
        self.add_ability('melee', self.row0['Cast'])

    def add_rotation(self, s):
        self.rotation_string = s
        for c in s:
            if c=='a':
                self.add_auto()
            elif c=='A':
                self.add_gcd_ability('arcane')
            elif c=='s':
                self.add_gcd_ability('steady')
            elif c=='m':
                self.add_gcd_ability('multi')
            elif c=='r':
                self.add_raptor()
            elif c=='w':
                self.add_melee() # white hit
            elif c=='h':
                self.ranged.haste = self.ranged.haste * 1.15 # manually proc imp hawk for testing


if __name__ == "__main__":
    r = rotationplot()
    r.init_fig()
    #r.add_rotation('asmasasAasas') # 5:5:1:1:1:1 french non-weave
    #r.add_rotation('asmarsasAawsas') # 5:5:1:1:1:1 french 2-weave
    #r.add_rotation('asmarsasAawsasaws') # 6:6:1:1:1:1 french 3-weave
    #r.add_rotation('asAarmasawsasasw') # 5:6:1:1
    #r.add_rotation('asmahrsasawsas') # 5:5:1:1:1:1 hawk after 2nd, skip arcane
    #r.add_rotation('rasaswmasasAwas') # 5:5:1:1:1:1
    #r.add_rotation('amwasaswasaswamaswasaswas') # 1:1 mw with multis
    #r.add_rotation('asasasasasasasasasas') # 1:1 mw
    #r.add_rotation('asmarsasAarsasahsrasasr') # 5:5:1:1:1:1
    r.add_rotation('asmasasAasas') # 5:5:1:1
    #r.add_rotation('hasmasasasasas') # 6:6:1
    #r.add_rotation('aswasasras')

    # r.add_rotation('as')
    #r.add_rotation('asmahsasasas') # 5:5:1:1 hawk after 2nd auto -> skip arcane, got to 1:1
    r.complete_fig()
