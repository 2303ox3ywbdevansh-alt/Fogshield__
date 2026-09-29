(() => {
 const canvas=document.getElementById('map'); if(!canvas)return; const ctx=canvas.getContext('2d');
 let state=null; window.drawHaulMap=s=>{state=s; draw()};
 function draw(){if(!state)return; const rect=canvas.getBoundingClientRect(),dpr=devicePixelRatio||1; canvas.width=rect.width*dpr;canvas.height=rect.height*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);let w=rect.width,h=rect.height;
 ctx.fillStyle='#0a1012';ctx.fillRect(0,0,w,h);let pts=state.road;let xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),minX=Math.min(...xs)-12,maxX=Math.max(...xs)+12,minY=Math.min(...ys)-8,maxY=Math.max(...ys)+8;let scale=Math.min(w/(maxX-minX),h/(maxY-minY)),ox=(w-(maxX-minX)*scale)/2,oy=(h-(maxY-minY)*scale)/2;let xy=p=>[ox+(p[0]-minX)*scale,oy+(p[1]-minY)*scale];
 // fog veil density is tied directly to the visibility control.
 ctx.fillStyle=`rgba(195,211,211,${Math.max(0,.24-state.visibility/450)})`;ctx.fillRect(0,0,w,h);
 for(const z of state.zones){let q=xy(z.center),r=z.radius*scale;ctx.beginPath();ctx.arc(q[0],q[1],r,0,Math.PI*2);ctx.fillStyle='rgba(240,184,79,.035)';ctx.fill();ctx.setLineDash([4,5]);ctx.strokeStyle='rgba(240,184,79,.43)';ctx.lineWidth=1;ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#988451';ctx.font='9px monospace';ctx.fillText(z.name.toUpperCase(),q[0]+5,q[1]-r+12)}
 ctx.beginPath();pts.forEach((p,i)=>{let q=xy(p);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.strokeStyle='#252f33';ctx.lineWidth=26;ctx.lineJoin='round';ctx.lineCap='round';ctx.stroke();ctx.beginPath();pts.forEach((p,i)=>{let q=xy(p);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.strokeStyle='#506167';ctx.lineWidth=2;ctx.setLineDash([6,7]);ctx.stroke();ctx.setLineDash([]);
 for(const [p,label,color] of [[pts[0],'LOAD','#c5f36d'],[pts[pts.length-1],'DUMP','#ff9d60']]){let q=xy(p);ctx.beginPath();ctx.arc(...q,6,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();ctx.fillStyle=color;ctx.font='bold 9px monospace';ctx.fillText(label,q[0]+9,q[1]-8)}
 for(const v of state.vehicles){let q=xy(v.position),color=v.alert==='critical'?'#ff5e62':v.alert==='warning'?'#f0b84f':v.alert==='caution'?'#e2d068':'#36d6bd';ctx.save();ctx.translate(...q);ctx.rotate(v.heading*Math.PI/180);ctx.fillStyle=color;ctx.shadowColor=color;ctx.shadowBlur=11;ctx.beginPath();ctx.roundRect(-7,-4,14,8,2);ctx.fill();ctx.fillStyle='#081111';ctx.beginPath();ctx.moveTo(4,-2.3);ctx.lineTo(10,0);ctx.lineTo(4,2.3);ctx.fill();ctx.restore();ctx.fillStyle='#c4d0d2';ctx.font='9px monospace';ctx.fillText(v.id,q[0]+7,q[1]-7)}
 }
 addEventListener('resize',draw);
})();
