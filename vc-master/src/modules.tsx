import {FormEvent, useEffect, useState} from 'react';
import {AlertTriangle, Building2, CheckCircle2, ClipboardList, Download, FileCheck2, MessageCircle, RefreshCw, Send, Upload, Users, XCircle} from 'lucide-react';
import {api, downloadFile, organizationApi} from './api';

type Profile={id:number;user:number;username:string;first_name:string;last_name:string;role:string};
type Message={id:number;sender:number;sender_name:string;recipient:number;recipient_name:string;body:string;created_at:string};
type CommunityRequest={id:number;requester_name:string;category:string;category_label:string;subject:string;description:string;status:string;status_label:string;created_at:string};
type BoardMember={id:number;full_name:string;role_name:string;assigned_at:string;active:boolean};
type Organization={name:string;rut:string;purpose:string;relation_funds:string;constitution_date:string;legal_representative:string;institution_type:string;thematic_area:string;legal_personality:string;assets:string;address:string;commune_name:string;province_name:string;region_name:string;board_members:BoardMember[]};
type ResidenceCertificate={id:number;requester_name:string;applicant_name:string;rut:string;address:string;commune:string;purpose:string;proof_type:string;proof_type_label:string;proof_extension:string;document_date:string;automatic_status:string;automatic_status_label:string;automatic_notes:string;status:string;status_label:string;reviewer_notes:string;reviewer_name:string;certificate_number:string|null;verification_code:string;verification_url:string;issued_at:string|null;created_at:string};

export function OrganizationView(){
  const[item,setItem]=useState<Organization|null>(null),[error,setError]=useState('');
  useEffect(()=>{organizationApi<Organization>('/institucion/mi-jdv-info/').then(setItem).catch(e=>setError((e as Error).message))},[]);
  if(error)return <ModuleEmpty title="Servicio de organización no disponible" text="Iniciar organizacion_core-master en el puerto 8001."/>;
  if(!item)return <ModuleEmpty title="Cargando organización" text="Consultando los datos oficiales de la junta de vecinos."/>;
  return <section className="page"><div className="page-heading"><h2>Conocer la organización</h2><p>Consultar identidad legal, ubicación y directiva vigente.</p></div><section className="org-grid"><article className="panel org-main"><div className="org-mark"><Building2/></div><div><small>{item.institution_type}</small><h3>{item.name}</h3><p>{item.purpose}</p></div></article><article className="panel detail-list"><h3>Información institucional</h3><dl><div><dt>RUT</dt><dd>{item.rut}</dd></div><div><dt>Representante legal</dt><dd>{item.legal_representative}</dd></div><div><dt>Personalidad jurídica</dt><dd>{item.legal_personality}</dd></div><div><dt>Constitución</dt><dd>{new Date(item.constitution_date+'T12:00:00').toLocaleDateString('es-CL')}</dd></div><div><dt>Dirección</dt><dd>{item.address}, {item.commune_name}</dd></div><div><dt>Territorio</dt><dd>{item.province_name}, {item.region_name}</dd></div></dl></article></section><article className="panel board"><h3>Directiva vigente</h3><div className="board-list">{item.board_members.map(member=><div key={member.id}><Users/><span><strong>{member.full_name}</strong><small>{member.role_name}</small></span></div>)}</div></article></section>
}

export function MessagesView(){
  const[people,setPeople]=useState<Profile[]>([]),[items,setItems]=useState<Message[]>([]),[recipient,setRecipient]=useState(''),[body,setBody]=useState(''),[notice,setNotice]=useState('');
  const load=()=>Promise.all([api<Profile[]>('/contacts/'),api<Message[]>('/messages/')]).then(([p,m])=>{setPeople(p);setItems(m);if(!recipient&&p.length)setRecipient(String(p[0].user))});
  useEffect(()=>{void load()},[]);
  async function send(e:FormEvent){e.preventDefault();setNotice('');try{await api('/messages/',{method:'POST',body:JSON.stringify({recipient:Number(recipient),body})});setBody('');setNotice('Mensaje enviado correctamente.');await load()}catch(error){setNotice((error as Error).message)}}
  return <section className="page"><div className="page-heading"><h2>Conversar con la comunidad</h2><p>Enviar mensajes privados a integrantes de la misma junta de vecinos.</p></div><form className="editor message-editor" onSubmit={send}><select required value={recipient} onChange={e=>setRecipient(e.target.value)}><option value="">Seleccionar persona</option>{people.map(person=><option value={person.user} key={person.user}>{person.first_name} {person.last_name} · {person.username}</option>)}</select><textarea required maxLength={2000} placeholder="Escribir un mensaje respetuoso y claro" value={body} onChange={e=>setBody(e.target.value)}/><button><Send/>Enviar mensaje</button>{notice&&<small>{notice}</small>}</form><div className="list message-list">{items.map(message=><article key={message.id}><MessageCircle/><div><h3>De {message.sender_name||'Usuario'} para {message.recipient_name||'Usuario'}</h3><p>{message.body}</p><small>{new Date(message.created_at).toLocaleString('es-CL')}</small></div></article>)}</div></section>
}

export function RequestsView({canManage}:{canManage:boolean}){
  const[items,setItems]=useState<CommunityRequest[]>([]),[subject,setSubject]=useState(''),[description,setDescription]=useState(''),[category,setCategory]=useState('certificate'),[notice,setNotice]=useState('');
  const load=()=>api<CommunityRequest[]>('/requests/').then(setItems);
  useEffect(()=>{void load()},[]);
  async function create(e:FormEvent){e.preventDefault();try{await api('/requests/',{method:'POST',body:JSON.stringify({category,subject,description})});setSubject('');setDescription('');setNotice('Solicitud enviada a la directiva.');await load()}catch(error){setNotice((error as Error).message)}}
  async function changeStatus(id:number,status:string){await api(`/requests/${id}/`,{method:'PATCH',body:JSON.stringify({status})});await load()}
  return <section className="page"><div className="page-heading"><h2>Gestionar solicitudes</h2><p>Registrar necesidades vecinales y seguir su estado de atención.</p></div><form className="editor two" onSubmit={create}><select value={category} onChange={e=>setCategory(e.target.value)}><option value="certificate">Certificado</option><option value="security">Seguridad</option><option value="social">Apoyo social</option><option value="infrastructure">Infraestructura</option><option value="other">Otro</option></select><input required placeholder="Asunto" value={subject} onChange={e=>setSubject(e.target.value)}/><textarea required placeholder="Explicar la solicitud" value={description} onChange={e=>setDescription(e.target.value)}/><button>Enviar solicitud</button>{notice&&<small>{notice}</small>}</form><div className="list request-list">{items.map(item=><article key={item.id}><ClipboardList/><div><small>{item.category_label} · {item.requester_name}</small><h3>{item.subject}</h3><p>{item.description}</p><span className={`status ${item.status}`}>{item.status_label}</span></div>{canManage&&<select value={item.status} onChange={e=>changeStatus(item.id,e.target.value)}><option value="received">Recibida</option><option value="in_progress">En gestión</option><option value="resolved">Resuelta</option></select>}</article>)}</div></section>
}

export function CertificatesView({canManage}:{canManage:boolean}){
  const[items,setItems]=useState<ResidenceCertificate[]>([]),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[proof,setProof]=useState<File|null>(null),[reviewNotes,setReviewNotes]=useState<Record<number,string>>({});
  const[form,setForm]=useState({rut:'12.345.678-5',address:'',commune:'Santiago',purpose:'',proof_type:'utility_bill',document_date:new Date().toISOString().slice(0,10),sworn_declaration:false});
  const load=()=>api<ResidenceCertificate[]>('/residence-certificates/').then(setItems).catch(error=>setNotice((error as Error).message));
  useEffect(()=>{void load()},[]);

  async function create(e:FormEvent<HTMLFormElement>){
    e.preventDefault();
    const formElement=e.currentTarget;
    if(!proof){setNotice('Seleccionar un comprobante de domicilio.');return}
    if(!form.sworn_declaration){setNotice('Aceptar la declaración de veracidad para continuar.');return}
    const payload=new FormData();
    Object.entries(form).forEach(([key,value])=>payload.append(key,String(value)));
    payload.append('proof_document',proof);
    setBusy(true);setNotice('');
    try{await api('/residence-certificates/',{method:'POST',body:payload});setNotice('Solicitud enviada. La directiva revisará los antecedentes.');setProof(null);setForm({...form,address:'',purpose:'',sworn_declaration:false});formElement.reset();await load()}catch(error){setNotice((error as Error).message)}finally{setBusy(false)}
  }

  async function review(id:number,action:'approve'|'request-changes'|'reject'){
    const reviewer_notes=reviewNotes[id]||'';
    if(action!=='approve'&&!reviewer_notes.trim()){setNotice('Escribir una observación antes de solicitar cambios o rechazar.');return}
    setBusy(true);setNotice('');
    try{await api(`/residence-certificates/${id}/${action}/`,{method:'POST',body:JSON.stringify({reviewer_notes})});setNotice(action==='approve'?'Certificado emitido correctamente.':'Solicitud actualizada.');await load()}catch(error){setNotice((error as Error).message)}finally{setBusy(false)}
  }

  async function downloadCertificate(item:ResidenceCertificate){
    try{await downloadFile(`/residence-certificates/${item.id}/download/`,`${item.certificate_number||'certificado-residencia'}.pdf`)}catch(error){setNotice((error as Error).message)}
  }

  async function downloadProof(item:ResidenceCertificate){
    try{await downloadFile(`/residence-certificates/${item.id}/proof/`,`respaldo-${item.id}.${item.proof_extension}`)}catch(error){setNotice((error as Error).message)}
  }

  return <section className="page certificates-page"><div className="page-heading"><h2>{canManage?'Revisar certificados de residencia':'Solicitar certificado de residencia'}</h2><p>{canManage?'Validar antecedentes y emitir documentos trazables.':'Adjuntar un comprobante para que la directiva revise y emita el certificado.'}</p></div>
    {!canManage&&<form className="editor two certificate-form" onSubmit={create}>
      <label>RUT<input required value={form.rut} onChange={e=>setForm({...form,rut:e.target.value})}/></label>
      <label>Comuna<input required value={form.commune} onChange={e=>setForm({...form,commune:e.target.value})}/></label>
      <label className="full">Domicilio completo<input required minLength={8} placeholder="Calle, número, villa o población" value={form.address} onChange={e=>setForm({...form,address:e.target.value})}/></label>
      <label>Tipo de comprobante<select value={form.proof_type} onChange={e=>setForm({...form,proof_type:e.target.value})}><option value="utility_bill">Cuenta de servicio básico</option><option value="lease">Contrato de arriendo</option><option value="bank_statement">Documento bancario o institucional</option><option value="other">Otro comprobante</option></select></label>
      <label>Fecha del comprobante<input required type="date" max={new Date().toISOString().slice(0,10)} value={form.document_date} onChange={e=>setForm({...form,document_date:e.target.value})}/></label>
      <label className="full">Finalidad<input required placeholder="Ejemplo: postulación a beneficio municipal" value={form.purpose} onChange={e=>setForm({...form,purpose:e.target.value})}/></label>
      <label className="file-field full"><Upload/><span>{proof?proof.name:'Adjuntar comprobante PDF, JPG o PNG · máximo 5 MB'}</span><input required type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={e=>setProof(e.target.files?.[0]||null)}/></label>
      <label className="declaration full"><input type="checkbox" checked={form.sworn_declaration} onChange={e=>setForm({...form,sworn_declaration:e.target.checked})}/><span>Declaro bajo juramento que los datos proporcionados son verdaderos y autorizo su revisión para emitir este certificado.</span></label>
      <button disabled={busy}><FileCheck2/>{busy?'Enviando...':'Enviar solicitud'}</button>
    </form>}
    {notice&&<div className="module-notice">{notice}</div>}
    <div className="certificate-list">{items.length===0&&<article className="panel empty"><FileCheck2/><h3>No existen solicitudes todavía</h3><p>Las solicitudes y certificados emitidos aparecerán en esta sección.</p></article>}{items.map(item=><article className="panel certificate-card" key={item.id}>
      <div className="certificate-title"><div className="certificate-icon"><FileCheck2/></div><div><small>Solicitud #{item.id} · {new Date(item.created_at).toLocaleDateString('es-CL')}</small><h3>{item.applicant_name}</h3><p>{item.address}, {item.commune}</p></div><span className={`status ${item.status}`}>{item.status_label}</span></div>
      <div className="certificate-details"><div><span>RUT</span><strong>{item.rut}</strong></div><div><span>Comprobante</span><strong>{item.proof_type_label}</strong></div><div><span>Fecha del respaldo</span><strong>{new Date(item.document_date+'T12:00:00').toLocaleDateString('es-CL')}</strong></div><div><span>Finalidad</span><strong>{item.purpose}</strong></div></div>
      <div className={`automatic-check ${item.automatic_status}`}><AlertTriangle/><div><strong>{item.automatic_status_label}</strong><p>{item.automatic_notes}</p></div></div>
      {item.reviewer_notes&&<div className="review-note"><strong>Observación de la directiva</strong><p>{item.reviewer_notes}</p></div>}
      {canManage&&item.status==='pending'&&<div className="review-panel"><textarea placeholder="Observación de la revisión" value={reviewNotes[item.id]||''} onChange={e=>setReviewNotes({...reviewNotes,[item.id]:e.target.value})}/><div className="certificate-actions"><button className="secondary" type="button" onClick={()=>downloadProof(item)}><Download/>Ver respaldo</button><button className="success" type="button" disabled={busy} onClick={()=>review(item.id,'approve')}><CheckCircle2/>Aprobar y emitir</button><button className="warning" type="button" disabled={busy} onClick={()=>review(item.id,'request-changes')}><RefreshCw/>Solicitar corrección</button><button className="reject" type="button" disabled={busy} onClick={()=>review(item.id,'reject')}><XCircle/>Rechazar</button></div></div>}
      {!canManage&&item.status==='needs_changes'&&<CorrectionForm item={item} done={async(message)=>{setNotice(message);await load()}}/>}
      {item.status==='issued'&&<div className="issued-panel"><div><CheckCircle2/><span><strong>{item.certificate_number}</strong><small>Emitido por {item.reviewer_name||'la directiva'}</small></span></div><div className="certificate-actions"><button className="success" type="button" onClick={()=>downloadCertificate(item)}><Download/>Descargar PDF</button>{item.verification_url&&<a href={item.verification_url} target="_blank" rel="noreferrer">Verificar autenticidad</a>}</div></div>}
    </article>)}</div>
  </section>
}

function CorrectionForm({item,done}:{item:ResidenceCertificate;done:(message:string)=>Promise<void>}){
  const[proof,setProof]=useState<File|null>(null),[date,setDate]=useState(new Date().toISOString().slice(0,10)),[busy,setBusy]=useState(false);
  async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();if(!proof)return;const data=new FormData();data.append('proof_document',proof);data.append('document_date',date);data.append('sworn_declaration','true');setBusy(true);try{await api(`/residence-certificates/${item.id}/resubmit/`,{method:'POST',body:data});await done('Antecedente corregido y reenviado a la directiva.')}catch(error){await done((error as Error).message)}finally{setBusy(false)}}
  return <form className="correction-form" onSubmit={submit}><strong>Adjuntar la corrección solicitada</strong><input required type="date" max={new Date().toISOString().slice(0,10)} value={date} onChange={e=>setDate(e.target.value)}/><input required type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={e=>setProof(e.target.files?.[0]||null)}/><button disabled={busy}><RefreshCw/>{busy?'Enviando...':'Reenviar antecedente'}</button></form>
}

function ModuleEmpty({title,text}:{title:string;text:string}){return <article className="panel empty"><Building2/><h2>{title}</h2><p>{text}</p></article>}
