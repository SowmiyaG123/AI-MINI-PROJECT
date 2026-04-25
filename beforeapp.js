import { useState, useEffect, useRef, useCallback } from "react";

const API = "http://localhost:8000";
const SID_KEY = "rcp_sid";
const getOrMakeSid = () => { let s = localStorage.getItem(SID_KEY); if (!s) { s = crypto.randomUUID(); localStorage.setItem(SID_KEY, s); } return s; };
const md = t => t.replace(/\*\*(.*?)\*\*/g, `<b style="color:#f5c76e">$1</b>`).replace(/\n/g, "<br/>");
const G = { bg:"#0e0f0f", surf:"#161818", alt:"#1d2020", bdr:"#272b2b", acc:"#e8a027", accD:"#b87d1a", accG:"rgba(232,160,39,.18)", txt:"#f0ede8", sub:"#9a9590", mut:"#5a5652", grn:"#3ecf8e", red:"#f06565", blu:"#5b9cf6", chip:"#222626" };

function Spinner(){ return <span style={{display:"inline-block",width:16,height:16,border:`2px solid ${G.bdr}`,borderTopColor:G.acc,borderRadius:"50%",animation:"spin .7s linear infinite"}}/>; }
function Pill({t,c}){ const bg=c==="g"?"#1a3328":c==="b"?"#1a2540":"#2e1f08",tc=c==="g"?G.grn:c==="b"?G.blu:"#f5c76e"; return <span style={{background:bg,color:tc,fontSize:10,fontWeight:700,padding:"2px 8px",borderRadius:20,textTransform:"uppercase",letterSpacing:".05em"}}>{t}</span>; }

function RecipeCard({ r, first }) {
  const [open, setOpen] = useState(first);
  const [tab, setTab] = useState("ingredients");
  const pct = r.match_pct;
  const barC = pct>=80?G.grn:pct>=50?G.acc:G.red;
  return (
    <div style={{background:G.alt,border:`1px solid ${open?G.accD:G.bdr}`,borderRadius:12,overflow:"hidden",marginBottom:8,boxShadow:open?`0 0 18px ${G.accG}`:"none",transition:"border .2s"}}>
      <button onClick={()=>setOpen(!open)} style={{width:"100%",display:"flex",alignItems:"center",gap:10,padding:"12px 14px",background:"none",border:"none",cursor:"pointer",textAlign:"left"}}>
        <div style={{flex:1}}>
          <div style={{display:"flex",gap:8,alignItems:"center",flexWrap:"wrap",marginBottom:4}}>
            <span style={{fontSize:14,fontWeight:700,color:G.txt,fontFamily:"Georgia,serif"}}>{r.name}</span>
            {first && <Pill t="Best Match" c="g"/>}
          </div>
          <div style={{display:"flex",gap:6,flexWrap:"wrap",alignItems:"center"}}>
            <Pill t={r.cuisine} c="b"/>
            {r.diet?.map(d=><Pill key={d} t={d} c="a"/>)}
            <span style={{fontSize:11,color:G.mut}}>⏱ {r.time} · 👤 {r.servings}</span>
          </div>
        </div>
        {pct!=null && <div style={{textAlign:"center",minWidth:50}}><div style={{fontSize:19,fontWeight:800,color:barC}}>{pct}%</div><div style={{fontSize:9,color:G.mut}}>match</div></div>}
        <span style={{color:G.mut,fontSize:16}}>{open?"▲":"▼"}</span>
      </button>
      {pct!=null && <div style={{padding:"0 14px 8px"}}><div style={{background:G.bdr,borderRadius:4,height:4,overflow:"hidden"}}><div style={{height:"100%",width:`${pct}%`,background:barC,borderRadius:4,transition:"width .6s ease"}}/></div></div>}
      {open && <>
        <div style={{display:"flex",borderTop:`1px solid ${G.bdr}`,borderBottom:`1px solid ${G.bdr}`}}>
          {["ingredients","steps","missing"].map(tb=>(
            <button key={tb} onClick={()=>setTab(tb)} style={{flex:1,padding:"9px 0",fontSize:11,fontWeight:700,letterSpacing:".05em",textTransform:"uppercase",background:tab===tb?G.accG:"transparent",color:tab===tb?G.acc:G.sub,border:"none",borderBottom:tab===tb?`2px solid ${G.acc}`:"2px solid transparent",cursor:"pointer"}}>{tb}</button>
          ))}
        </div>
        <div style={{padding:"12px 14px"}}>
          {tab==="ingredients" && <div style={{display:"flex",flexWrap:"wrap",gap:6}}>{Object.entries(r.ingredients).map(([k,v])=>(
            <span key={k} style={{background:G.chip,border:`1px solid ${G.bdr}`,borderRadius:20,padding:"3px 10px",fontSize:11,color:G.txt}}><b style={{color:G.acc}}>{k}</b><span style={{color:G.mut}}> · {v}</span></span>
          ))}</div>}
          {tab==="steps" && <ol style={{listStyle:"none",padding:0,margin:0,display:"flex",flexDirection:"column",gap:8}}>{r.steps.map((s,i)=>(
            <li key={i} style={{display:"flex",gap:10,alignItems:"flex-start"}}><span style={{minWidth:22,height:22,background:G.acc,color:"#000",borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",fontSize:10,fontWeight:800,flexShrink:0}}>{i+1}</span><span style={{fontSize:12,color:G.sub,lineHeight:1.6}}>{s}</span></li>
          ))}</ol>}
          {tab==="missing" && (r.missing?.length>0
            ? <div><p style={{color:G.mut,fontSize:11,marginBottom:8}}>Missing ingredients — ask me for substitutes!</p><div style={{display:"flex",flexWrap:"wrap",gap:6}}>{r.missing.map(m=><span key={m} style={{background:"#2a1515",border:`1px solid ${G.red}33`,color:G.red,borderRadius:20,padding:"3px 10px",fontSize:11}}>⚠ {m}</span>)}</div></div>
            : <p style={{color:G.grn,fontSize:12}}>✅ You have all the ingredients!</p>
          )}
        </div>
      </>}
    </div>
  );
}

function SubCard({ sub }) {
  if (!sub?.options) return null;
  return (
    <div style={{background:"#1a1f1a",border:`1px solid ${G.grn}44`,borderRadius:12,padding:14,marginTop:8}}>
      <div style={{fontSize:12,fontWeight:700,color:G.grn,marginBottom:8}}>🔄 Substitutes for "{sub.ingredient}"</div>
      <div style={{display:"flex",flexDirection:"column",gap:6}}>
        {sub.options.map((o,i)=><div key={i} style={{background:G.chip,borderRadius:8,padding:"8px 10px",fontSize:12,color:G.sub}}><span style={{color:G.txt,fontWeight:600}}>#{i+1}</span> {o}</div>)}
      </div>
    </div>
  );
}

function Message({ m }) {
  const isU = m.role==="user";
  return (
    <div style={{display:"flex",justifyContent:isU?"flex-end":"flex-start",marginBottom:14,gap:8,alignItems:"flex-start"}}>
      {!isU && <div style={{width:32,height:32,borderRadius:"50%",background:`linear-gradient(135deg,${G.acc},${G.accD})`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:15,flexShrink:0}}>🍳</div>}
      <div style={{maxWidth:"83%",display:"flex",flexDirection:"column",gap:6}}>
        <div style={{background:isU?`linear-gradient(135deg,${G.acc},${G.accD})`:G.surf,border:isU?"none":`1px solid ${G.bdr}`,borderRadius:isU?"18px 18px 4px 18px":"18px 18px 18px 4px",padding:"10px 14px",fontSize:13,lineHeight:1.65,color:isU?"#000":G.txt,fontWeight:isU?600:400}}>
          {isU ? m.text : <span dangerouslySetInnerHTML={{__html:md(m.text)}}/>}
        </div>
        {m.recipes?.length>0 && <div>{m.recipes.map((r,i)=><RecipeCard key={r.id} r={r} first={i===0}/>)}</div>}
        {m.sub && <SubCard sub={m.sub}/>}
        <span style={{fontSize:10,color:G.mut,alignSelf:isU?"flex-end":"flex-start"}}>{m.ts}</span>
      </div>
      {isU && <div style={{width:32,height:32,borderRadius:"50%",background:G.chip,border:`1px solid ${G.bdr}`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:13,flexShrink:0}}>👤</div>}
    </div>
  );
}

const QUICK = ["I have chicken, rice, and tomatoes","Apple dessert ideas","Substitute for paneer","No beef, vegetarian Italian","I have eggs, bread and butter","Salmon with lemon and garlic"];

export default function App() {
  const [sid] = useState(getOrMakeSid);
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [prefs, setPrefs] = useState({exclude:[],diet:[]});
  const [status, setStatus] = useState("checking");
  const endRef = useRef(null);
  const fileRef = useRef(null);
  const inpRef = useRef(null);

  useEffect(()=>{ endRef.current?.scrollIntoView({behavior:"smooth"}); },[msgs,loading]);

  useEffect(()=>{
    fetch(`${API}/health`).then(r=>r.ok?setStatus("online"):setStatus("error")).catch(()=>setStatus("offline"));
    setMsgs([{id:"w",role:"assistant",text:"👋 Welcome! Tell me what ingredients you have and I'll find the perfect recipe.\n\nTry: *'I have chicken, rice, garlic'* or upload a photo 📷",recipes:[],ts:now()}]);
  },[]);

  const now = ()=>new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});

  const send = useCallback(async(txt)=>{
    const t=(txt||input).trim(); if(!t||loading)return;
    setInput(""); setLoading(true);
    setMsgs(p=>[...p,{id:Date.now(),role:"user",text:t,recipes:[],ts:now()}]);
    try {
      const res = await fetch(`${API}/chat`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:sid,message:t})});
      const d = await res.json();
      setPrefs(d.preferences||{});
      setMsgs(p=>[...p,{id:Date.now()+1,role:"assistant",text:d.message,recipes:d.recipes||[],sub:d.sub,ts:now()}]);
    } catch(e){ setMsgs(p=>[...p,{id:Date.now()+1,role:"assistant",text:"⚠️ Backend unreachable. Run `python backend.py` on port 8000.",recipes:[],ts:now()}]); }
    finally{ setLoading(false); inpRef.current?.focus(); }
  },[input,loading,sid]);

  const uploadImg = async e=>{
    const f=e.target.files[0]; if(!f)return;
    setLoading(true);
    setMsgs(p=>[...p,{id:Date.now(),role:"user",text:`📸 ${f.name}`,recipes:[],ts:now()}]);
    const form=new FormData(); form.append("file",f); form.append("session_id",sid);
    try{
      const res=await fetch(`${API}/ocr`,{method:"POST",body:form});
      const d=await res.json();
      setMsgs(p=>[...p,{id:Date.now()+1,role:"assistant",text:d.message,recipes:d.recipes||[],ts:now()}]);
    }catch{ setMsgs(p=>[...p,{id:Date.now()+1,role:"assistant",text:"⚠️ OCR failed. Type ingredients instead.",recipes:[],ts:now()}]); }
    finally{ setLoading(false); e.target.value=""; }
  };

  const reset = async()=>{
    await fetch(`${API}/reset`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:sid})}).catch(()=>{});
    setPrefs({exclude:[],diet:[]}); setMsgs([{id:"r",role:"assistant",text:"🔄 Session reset! What are we cooking?",recipes:[],ts:now()}]);
  };

  const sc=status==="online"?G.grn:status==="checking"?G.acc:G.red;
  const allPrefs=[...(prefs.exclude||[]).map(e=>`🚫 ${e}`),(prefs.diet||[]).map(d=>`🥗 ${d}`)].flat();

  return (<>
    <style>{`*{box-sizing:border-box;margin:0;padding:0}body{background:${G.bg};font-family:'DM Sans',sans-serif;color:${G.txt};height:100vh;overflow:hidden}
    ::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:${G.bdr};border-radius:10px}
    @keyframes spin{to{transform:rotate(360deg)}}@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
    .mi{animation:fadeUp .22s ease both}.qb:hover{background:${G.accG}!important;border-color:${G.acc}!important;color:${G.acc}!important}
    .sb:hover:not(:disabled){background:${G.accD}!important}.sb:disabled{opacity:.4;cursor:not-allowed}textarea{resize:none}textarea:focus{outline:none}`}</style>

    <div style={{display:"flex",flexDirection:"column",height:"100vh",maxWidth:860,margin:"0 auto"}}>
      {/* Header */}
      <div style={{padding:"12px 18px",background:G.surf,borderBottom:`1px solid ${G.bdr}`,display:"flex",alignItems:"center",justifyContent:"space-between",flexShrink:0}}>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <div style={{width:40,height:40,borderRadius:11,background:`linear-gradient(135deg,${G.acc},${G.accD})`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:20,boxShadow:`0 0 16px ${G.accG}`}}>🍳</div>
          <div><div style={{fontFamily:"Georgia,serif",fontSize:16,fontWeight:700}}>Recipe Assistant</div><div style={{fontSize:10,color:G.mut}}>Groq LLaMA-3 · ChromaDB · Hybrid Ranking</div></div>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <span style={{width:7,height:7,borderRadius:"50%",background:sc,display:"inline-block",boxShadow:`0 0 5px ${sc}`}}/>
          <span style={{fontSize:11,color:G.mut}}>{status==="online"?"API Online":status==="checking"?"Connecting…":"Offline"}</span>
          <button onClick={reset} style={{background:G.chip,border:`1px solid ${G.bdr}`,borderRadius:7,color:G.sub,fontSize:11,padding:"4px 9px",cursor:"pointer"}}>↺ Reset</button>
        </div>
      </div>

      {/* Pref pills */}
      {allPrefs.length>0 && <div style={{display:"flex",flexWrap:"wrap",gap:5,padding:"6px 14px",background:G.surf,borderBottom:`1px solid ${G.bdr}`}}>
        {allPrefs.map(p=><span key={p} style={{background:"#1e1515",border:`1px solid ${G.red}44`,color:"#f0aaaa",borderRadius:20,padding:"2px 9px",fontSize:10,fontWeight:600}}>{p}</span>)}
      </div>}

      {/* Chat */}
      <div style={{flex:1,overflowY:"auto",padding:"18px 14px 4px"}}>
        {msgs.map((m,i)=><div key={m.id} className="mi"><Message m={m}/></div>)}
        {loading && <div style={{display:"flex",gap:8,alignItems:"center",marginBottom:12}}>
          <div style={{width:32,height:32,borderRadius:"50%",background:`linear-gradient(135deg,${G.acc},${G.accD})`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:15}}>🍳</div>
          <div style={{background:G.surf,border:`1px solid ${G.bdr}`,borderRadius:"18px 18px 18px 4px",padding:"10px 14px",display:"flex",gap:8,alignItems:"center"}}>
            <Spinner/><span style={{fontSize:12,color:G.mut}}>Searching recipes…</span>
          </div>
        </div>}
        {msgs.length<=1 && !loading && <div style={{paddingLeft:40,marginBottom:16}}>
          <p style={{fontSize:11,color:G.mut,marginBottom:8}}>💡 Try asking:</p>
          <div style={{display:"flex",flexWrap:"wrap",gap:6}}>
            {QUICK.map(q=><button key={q} className="qb" onClick={()=>send(q)} style={{background:G.chip,border:`1px solid ${G.bdr}`,borderRadius:20,color:G.sub,fontSize:11,padding:"5px 12px",cursor:"pointer",transition:"all .15s"}}>{q}</button>)}
          </div>
        </div>}
        <div ref={endRef}/>
      </div>

      {/* Input */}
      <div style={{padding:"10px 14px 14px",background:G.surf,borderTop:`1px solid ${G.bdr}`,flexShrink:0}}>
        <div style={{display:"flex",gap:7,alignItems:"flex-end",background:G.alt,border:`1px solid ${G.bdr}`,borderRadius:13,padding:"7px 9px 7px 13px"}}>
          <button onClick={()=>fileRef.current?.click()} disabled={loading} title="Upload ingredient photo" style={{width:33,height:33,borderRadius:9,border:"none",background:G.chip,color:G.sub,fontSize:16,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>📷</button>
          <input type="file" ref={fileRef} accept="image/*" onChange={uploadImg} style={{display:"none"}}/>
          <textarea ref={inpRef} value={input} onChange={e=>setInput(e.target.value)}
            onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();}}}
            onInput={e=>{e.target.style.height="auto";e.target.style.height=Math.min(e.target.scrollHeight,110)+"px";}}
            placeholder="Type ingredients, ask for a recipe, or request substitutes…" rows={1}
            style={{flex:1,background:"transparent",border:"none",color:G.txt,fontSize:13,lineHeight:1.5,fontFamily:"inherit",padding:"6px 0",maxHeight:110,overflowY:"auto"}}/>
          <button className="sb" onClick={()=>send()} disabled={!input.trim()||loading} style={{width:34,height:34,borderRadius:9,border:"none",background:G.acc,color:"#000",fontSize:16,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,transition:"background .15s",fontWeight:700}}>➤</button>
        </div>
        <p style={{textAlign:"center",fontSize:10,color:G.mut,marginTop:5}}>Enter to send · Shift+Enter for new line · 📷 to scan labels</p>
      </div>
    </div>
  </>);
}
