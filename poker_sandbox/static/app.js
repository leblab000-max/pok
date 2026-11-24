'use strict';
const $=id=>document.getElementById(id), token=document.querySelector('meta[name="poker-token"]').content;
let state=null, busy=false, initialized=false, commandVersion=0;
const labels={ready:'Готов к запуску',running:'AI играет',paused:'Пауза',stopped:'Остановлено · нужен сброс',completed:'Турнир завершён',error:'Ошибка · игра остановлена'};
const suit={s:'♠',h:'♥',d:'♦',c:'♣'};
function card(value){const el=document.createElement('span');el.className='card'+(value&&'hd'.includes(value[1])?' red':'')+(!value?' back':'');el.textContent=value?(value[0]==='T'?'10':value[0])+suit[value[1]]:'♠';return el;}
function cards(el,values,n){el.replaceChildren(...Array.from({length:n},(_,i)=>card(values[i])));}
function text(el,value){$(el).textContent=value;}
function notice(message){$('notice').hidden=!message;$('notice').textContent=message||'';}
async function api(path,body){const response=await fetch('/api/'+path,{method:body===undefined?'GET':'POST',headers:{'X-Poker-Token':token,'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});const result=await response.json();if(!response.ok)throw Error(result.error||response.status);return result;}
function configuration(){return {strategy:$('strategy').value,players:Number($('players').value),profile:$('profile').value,seed:Number($('seed').value),samples:Number($('samples').value),delay:Number($('delay').value)};}
async function command(name,body={}){
 if(busy&&name!=='stop')return;
 const version=++commandVersion;busy=true;render(state);
 try{
  if(name==='start'&&state.status==='ready'){
   await api('reset',configuration());
   if(version!==commandVersion)return;
  }
  const result=await api(name,body);
  if(version===commandVersion){render(result);notice('');}
 }catch(e){if(version===commandVersion)notice(e.message);}
 finally{if(version===commandVersion){busy=false;render(state);}}
}
for(const name of ['start','pause','stop','step'])$(name).onclick=()=>command(name);
$('reset').onclick=()=>command('reset',configuration());
for(const el of document.querySelectorAll('[data-action]'))el.onclick=()=>{const action=el.dataset.action;command('action',{pending_id:state.pending.id,action,...(['bet','raise'].includes(action)?{amount:Number($('amount').value)}:{})});};
function render(s){state=s;if(!initialized){for(const k of ['strategy','players','profile','seed','samples','delay'])$(k).value=s.config[k];initialized=true;}
$('status').className='status '+s.status;text('status',labels[s.status]||s.status);
$('start').disabled=busy||!['ready','paused'].includes(s.status);$('start').textContent=s.status==='paused'?'▶ Продолжить':'▶ Запустить';$('pause').disabled=busy||s.status!=='running';$('stop').disabled=!['running','paused','ready'].includes(s.status);$('step').disabled=busy||s.status!=='paused';$('reset').disabled=busy;
for(const el of document.querySelectorAll('.configuration input,.configuration select'))el.disabled=busy||!['ready','stopped','completed','error'].includes(s.status);
text('hand',`Раздача ${s.hand||'—'} · блайнды ${Math.floor(s.blind/2)} / ${s.blind}`);text('street',['Префлоп','','','Флоп','Тёрн','Ривер'][s.board.length]||'Ожидание');
$('pot').replaceChildren(document.createTextNode('БАНК '),Object.assign(document.createElement('strong'),{textContent:s.pot.toLocaleString('ru-RU')}));cards($('board'),s.board,5);cards($('hero'),s.hero_cards,2);
const tableWidth=document.querySelector('.table-wrap').clientWidth;const radius=Math.min(42,50-100*(innerWidth<=520?42:65)/tableWidth);
const seats=[];for(let i=0;i<s.config.players;i++){const seat=document.createElement('div');const angle=(90+360*i/s.config.players)*Math.PI/180;seat.className='seat'+(s.actor===i?' acting':'')+(s.folded.includes(i)?' folded':'')+(i===0?' hero-seat':'');seat.style.left=(50+radius*Math.cos(angle))+'%';seat.style.top=(50+39*Math.sin(angle))+'%';const name=document.createElement('div');name.className='seat-name';name.textContent=i===0?'ВЫ · AI':`AI ${i+1}`;const badges=document.createElement('span');badges.className='badges';badges.textContent=[s.button===i?'D':'',s.sb===i?'SB':'',s.bb===i?'BB':''].filter(Boolean).join(' ');name.append(badges);const chips=document.createElement('strong');chips.textContent=(s.stacks[String(i)]||0).toLocaleString('ru-RU');const hand=document.createElement('div');hand.className='cards mini';cards(hand,i===0?s.hero_cards:[],2);seat.append(name,chips,hand);seats.push(seat);}$('seats').replaceChildren(...seats);
const pending=s.pending,manual=s.status==='paused'&&pending?.seat===0,c=manual?pending.controls:null;
for(const el of document.querySelectorAll('[data-action]'))el.disabled=busy||!c||!c[({'raise':'raise_','all-in':'all_in'})[el.dataset.action]||el.dataset.action];
$('amount').disabled=!manual;text('bounds',c?.minimum!=null?`${c.minimum}–${c.maximum}`:'Рейз недоступен');if(c?.minimum!=null){$('amount').min=c.minimum;$('amount').max=c.maximum;if(!$('amount').value||Number($('amount').value)<c.minimum||Number($('amount').value)>c.maximum)$('amount').value=c.minimum;}
text('manual-hint',manual?'Ваш ход · можно применить действие':s.status==='paused'?'Шаг AI — перейти к следующему ходу':'Пауза на ходу места 1 — ручное действие');
const detail=pending?.seat===0&&pending.recommendation?pending.recommendation:s.last_decision;
if(detail){text('chosen-label',pending?.seat===0&&pending.recommendation?'Рекомендация · ещё не применена':'Последнее действие · #'+(detail.observation.hand_id+1)+' · '+(detail.source==='manual'?'вручную':'AI'));text('chosen',detail.decision.action.toUpperCase()+(detail.decision.raise_to!=null?' → '+detail.decision.raise_to:''));text('decision-time',detail.decision_ms.toFixed(1)+' мс · стратегия');text('reason',detail.reason);for(const [id,key]of [['equity','equity'],['win','win'],['tie','tie']])text(id,(detail.diagnostic[key]*100).toFixed(1)+'%');text('estimate-note',`Оценка перед этим действием (${({0:'префлоп',3:'флоп',4:'тёрн',5:'ривер'})[detail.observation.board.length]}). ${detail.diagnostic.samples} MC samples · равномерные неизвестные руки. Equity — доля банка, включая делёж. Отдельная диагностика, не оценка диапазонов стратегии.`);}
else{for(const id of ['chosen','equity','win','tie'])text(id,'—');text('decision-time','Расчёт ещё не выполнен');text('reason',s.status==='ready'?'Нажмите «Запустить». AI использует существующие алгоритмы проекта.':'Ожидание хода места 1. Скрытые расчёты соперников не отображаются.');}
text('hands',s.stats.hands);text('actions',s.stats.hero_actions);text('delta',(s.stats.hero_chip_delta>0?'+':'')+s.stats.hero_chip_delta);text('place',`${s.stats.place||'—'} / ${s.stats.tournaments}`);const total=Object.values(s.stacks).reduce((a,b)=>a+b,0)+s.pot;text('invariant',`Фишки + банк: ${total.toLocaleString('ru-RU')} / ${s.initial_chips.toLocaleString('ru-RU')}`);
const rows=s.events.slice(-40).reverse().map(e=>{const row=document.createElement('div');row.className='log-row '+(e.kind==='error'?'log-error':'');let values=[new Date(e.at*1000).toLocaleTimeString('ru-RU')+` / #${e.hand||s.hand}`,e.seat===0?'Вы · AI':e.seat!=null?'AI '+(e.seat+1):'Стол',e.kind==='action'?(e.all_in?'ALL-IN':e.action.toUpperCase()):e.kind==='hand'?'Раздача завершена':e.kind==='tournament'?'Турнир завершён':e.message,e.paid??'—'];for(const v of values){const span=document.createElement('span');span.textContent=v;row.append(span);}return row;});if(rows.length)$('events').replaceChildren(...rows);else $('events').replaceChildren(Object.assign(document.createElement('p'),{className:'empty',textContent:'Пока нет игровых событий. Сессия готова к запуску.'}));
if(s.error)notice(s.error);
}
async function poll(){try{if(!busy){const version=commandVersion;const result=await api('state');if(!busy&&version===commandVersion)render(result);}}catch(e){notice('Связь с локальным сервером потеряна: '+e.message);}setTimeout(poll,200);}poll();
