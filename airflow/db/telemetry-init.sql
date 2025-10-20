create table if not exists events
(
    event_id    bigserial primary key,
    customer_id bigint    not null,
    event_type  text      not null, --- 'accuracy' | 'movement' | 'intensity'
    event_value numeric,            --- 'intensity' aggregation
    event_time  timestamp not null default now()
);

create index if not exists idx_events_customer_time on events (customer_id, event_time);

insert into events (customer_id, event_type, event_value, event_time)
values (1001, 'accuracy', null, now() - interval '1 day'),
       (1001, 'movement', null, now() - interval '3 hours'),
       (1001, 'intensity', 0.7, now() - interval '2 hours'),
       (1002, 'movement', null, now() - interval '4 hours'),
       (1002, 'intensity', 1.2, now() - interval '1 hour');
