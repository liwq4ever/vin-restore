// VIN-FRAME-V1 Rev A. Units mm; CAD Z=0 at metal underside.
// Reference contact plane Z=-1.3; nominal marker Z=3 + coating.
// Pilot holes are simplified, NOT modeled threads. Refer to PDF for blind drilling.
$fn=64;
part="assembly"; // "body", "pad", "handle", "assembly"
module rr(w,h,r,z){ linear_extrude(height=z) hull(){for(x=[r,w-r])for(y=[r,h-r])translate([x,y])circle(r=r);} }
module body(){difference(){rr(260,70,4,3);translate([20,20,-1])rr(220,30,3,5);
for(p=[[10,10],[250,10],[130,60]]){translate([p[0],p[1],-.01])cylinder(d=8.02,h=.21);translate([p[0],p[1],.2])cylinder(d=1.6,h=2.2);}
for(p=[[10,22],[10,48],[250,22],[250,48]])translate([p[0],p[1],.5])cylinder(d=2.5,h=2.51);}}
module pad(){difference(){cylinder(d=7.98,h=1.5);translate([0,0,-.01])cylinder(d=2.2,h=1.52);cylinder(d1=4.3,d2=2.2,h=1.05);}}
module handle(){difference(){union(){translate([-15,18,0])cube([30,8,3]);translate([-15,44,0])cube([30,8,3]);translate([-15,18,0])cube([8,34,15]);}for(p=[[10,22],[10,48]])translate([p[0],p[1],-.1])cylinder(d=3.4,h=3.2);}}
if(part=="body")body();if(part=="pad")pad();if(part=="handle")handle();
if(part=="assembly"){color("silver")body();for(p=[[10,10],[250,10],[130,60]])color("tan")translate([p[0],p[1],-1.3])pad();color("steelblue")translate([0,0,3])handle();color("steelblue")translate([260,70,3])rotate([0,0,180])handle();}
