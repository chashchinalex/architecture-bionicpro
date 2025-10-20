create table if not exists customers
(
    customer_id bigint primary key,
    email       text      not null,
    first_name  text,
    last_name   text,
    created_at  timestamp not null default now(),
    updated_at  timestamp not null default now()
);

insert into customers (customer_id, email, first_name, last_name)
values (1001, 'alice@example.com', 'Alice', 'Green'),
       (1002, 'bob@example.com', 'Bob', 'Brown')
on conflict do nothing;
