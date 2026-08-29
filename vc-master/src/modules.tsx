import {FormEvent, useEffect, useState} from 'react';
import {Building2, ClipboardList, MessageCircle, Send, Users} from 'lucide-react';
import {api, organizationApi} from './api';

type Profile={id:number;user:number;username:string;first_name:string;last_name:string;role:string};
type Message={id:number;sender:number;sender_name:string;recipient:number;recipient_name:string;body:string;created_at:string};
type CommunityRequest={id:number;requester_name:string;category:string;category_label:string;subject:string;description:string;status:string;status_label:string;created_at:string};
type BoardMember={id:number;full_name:string;role_name:string;assigned_at:string;active:boolean};
type Organization={name:string;rut:string;purpose:string;relation_funds:string;constitution_date:string;legal_representative:string;institution_type:string;thematic_area:string;legal_personality:string;assets:string;address:string;commune_name:string;province_name:string;region_name:string;board_members:BoardMember[]};

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

function ModuleEmpty({title,text}:{title:string;text:string}){return <article className="panel empty"><Building2/><h2>{title}</h2><p>{text}</p></article>}
