-- This schema is for reference only.
-- Table order and constraints may not be valid for execution.
-- ORM Model to SQL Schema

CREATE TABLE public.LOTES_lot (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  code character varying NOT NULL UNIQUE,
  area_m2 numeric NOT NULL,
  price numeric NOT NULL,
  image character varying,
  status character varying NOT NULL,
  description text,
  latitude double precision NOT NULL,
  longitude double precision NOT NULL,
  stage_id bigint NOT NULL,
  CONSTRAINT LOTES_lot_pkey PRIMARY KEY (id),
  CONSTRAINT LOTES_lot_stage_id_84be19c6_fk_LOTES_stage_id FOREIGN KEY (stage_id) REFERENCES public.LOTES_stage(id)
);
CREATE TABLE public.LOTES_lotimage (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  image character varying NOT NULL,
  created_at timestamp with time zone NOT NULL,
  lot_id bigint NOT NULL,
  CONSTRAINT LOTES_lotimage_pkey PRIMARY KEY (id),
  CONSTRAINT LOTES_lotimage_lot_id_5eee96c2_fk_LOTES_lot_id FOREIGN KEY (lot_id) REFERENCES public.LOTES_lot(id)
);
CREATE TABLE public.LOTES_stage (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  name character varying NOT NULL,
  description text NOT NULL,
  CONSTRAINT LOTES_stage_pkey PRIMARY KEY (id)
);
CREATE TABLE public.PQRS_pqrs (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  type character varying NOT NULL,
  message text NOT NULL,
  response text,
  status character varying NOT NULL,
  client_id bigint NOT NULL,
  CONSTRAINT PQRS_pqrs_pkey PRIMARY KEY (id),
  CONSTRAINT PQRS_pqrs_client_id_74515c87_fk_USERS_user_id FOREIGN KEY (client_id) REFERENCES public.USERS_user(id)
);
CREATE TABLE public.PROJECT_INFO_projectinfo (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  title character varying NOT NULL,
  description text NOT NULL,
  CONSTRAINT PROJECT_INFO_projectinfo_pkey PRIMARY KEY (id)
);
CREATE TABLE public.SALES_payment (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  amount numeric NOT NULL,
  payment_date date NOT NULL,
  is_validated boolean NOT NULL,
  purchase_id bigint NOT NULL,
  CONSTRAINT SALES_payment_pkey PRIMARY KEY (id),
  CONSTRAINT SALES_payment_purchase_id_76d7ca83_fk_SALES_purchase_id FOREIGN KEY (purchase_id) REFERENCES public.SALES_purchase(id)
);
CREATE TABLE public.SALES_purchase (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  total_amount numeric NOT NULL,
  created_at timestamp with time zone NOT NULL,
  is_validated boolean NOT NULL,
  client_id bigint NOT NULL,
  CONSTRAINT SALES_purchase_pkey PRIMARY KEY (id),
  CONSTRAINT SALES_purchase_client_id_770e24db_fk_USERS_user_id FOREIGN KEY (client_id) REFERENCES public.USERS_user(id)
);
CREATE TABLE public.SALES_purchase_lots (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  purchase_id bigint NOT NULL,
  lot_id bigint NOT NULL,
  CONSTRAINT SALES_purchase_lots_pkey PRIMARY KEY (id),
  CONSTRAINT SALES_purchase_lots_purchase_id_e4397725_fk_SALES_purchase_id FOREIGN KEY (purchase_id) REFERENCES public.SALES_purchase(id),
  CONSTRAINT SALES_purchase_lots_lot_id_14a434cf_fk_LOTES_lot_id FOREIGN KEY (lot_id) REFERENCES public.LOTES_lot(id)
);
CREATE TABLE public.USERS_user (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  password character varying NOT NULL,
  last_login timestamp with time zone,
  is_superuser boolean NOT NULL,
  username character varying NOT NULL UNIQUE,
  first_name character varying NOT NULL,
  last_name character varying NOT NULL,
  email character varying NOT NULL,
  is_staff boolean NOT NULL,
  is_active boolean NOT NULL,
  date_joined timestamp with time zone NOT NULL,
  role character varying NOT NULL,
  document_number character varying,
  phone_number character varying,
  CONSTRAINT USERS_user_pkey PRIMARY KEY (id)
);
CREATE TABLE public.USERS_user_groups (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  user_id bigint NOT NULL,
  group_id integer NOT NULL,
  CONSTRAINT USERS_user_groups_pkey PRIMARY KEY (id),
  CONSTRAINT USERS_user_groups_user_id_0ba86593_fk_USERS_user_id FOREIGN KEY (user_id) REFERENCES public.USERS_user(id),
  CONSTRAINT USERS_user_groups_group_id_339ac64f_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id)
);
CREATE TABLE public.USERS_user_user_permissions (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  user_id bigint NOT NULL,
  permission_id integer NOT NULL,
  CONSTRAINT USERS_user_user_permissions_pkey PRIMARY KEY (id),
  CONSTRAINT USERS_user_user_permissions_user_id_9b4a3173_fk_USERS_user_id FOREIGN KEY (user_id) REFERENCES public.USERS_user(id),
  CONSTRAINT USERS_user_user_perm_permission_id_65156bee_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id)
);
CREATE TABLE public.auth_group (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  name character varying NOT NULL UNIQUE,
  CONSTRAINT auth_group_pkey PRIMARY KEY (id)
);
CREATE TABLE public.auth_group_permissions (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  group_id integer NOT NULL,
  permission_id integer NOT NULL,
  CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id),
  CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id),
  CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id)
);
CREATE TABLE public.auth_permission (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  name character varying NOT NULL,
  content_type_id integer NOT NULL,
  codename character varying NOT NULL,
  CONSTRAINT auth_permission_pkey PRIMARY KEY (id),
  CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id)
);
CREATE TABLE public.django_admin_log (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  action_time timestamp with time zone NOT NULL,
  object_id text,
  object_repr character varying NOT NULL,
  action_flag smallint NOT NULL CHECK (action_flag >= 0),
  change_message text NOT NULL,
  content_type_id integer,
  user_id bigint NOT NULL,
  CONSTRAINT django_admin_log_pkey PRIMARY KEY (id),
  CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id),
  CONSTRAINT django_admin_log_user_id_c564eba6_fk_USERS_user_id FOREIGN KEY (user_id) REFERENCES public.USERS_user(id)
);
CREATE TABLE public.django_content_type (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  app_label character varying NOT NULL,
  model character varying NOT NULL,
  CONSTRAINT django_content_type_pkey PRIMARY KEY (id)
);
CREATE TABLE public.django_migrations (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  app character varying NOT NULL,
  name character varying NOT NULL,
  applied timestamp with time zone NOT NULL,
  CONSTRAINT django_migrations_pkey PRIMARY KEY (id)
);
CREATE TABLE public.django_session (
  session_key character varying NOT NULL,
  session_data text NOT NULL,
  expire_date timestamp with time zone NOT NULL,
  CONSTRAINT django_session_pkey PRIMARY KEY (session_key)
);